from maxo.routing.ctx import Ctx
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter, BaseFilter
from maxo.routing.filters.logic import (
    AndFilter,
    InvertFilter,
    OrFilter,
    combine_filters,
)
from maxo.routing.interfaces.filter import Filter
from maxo.types.base import BaseUpdate

TrueF = AlwaysTrueFilter
FalseF = AlwaysFalseFilter


class WritingFilter(BaseFilter[BaseUpdate]):
    def __init__(self, key: str, value: str, *, result: bool = True) -> None:
        self._key = key
        self._value = value
        self._result = result

    async def __call__(self, update: BaseUpdate, ctx: Ctx) -> bool:
        ctx[self._key] = self._value
        return self._result


async def test_and_filter() -> None:
    assert await AndFilter(TrueF(), TrueF())(BaseUpdate(), Ctx({})) is True
    assert await AndFilter(TrueF(), FalseF())(BaseUpdate(), Ctx({})) is False
    assert await AndFilter(FalseF(), TrueF())(BaseUpdate(), Ctx({})) is False
    assert await AndFilter(FalseF(), FalseF())(BaseUpdate(), Ctx({})) is False


async def test_or_filter() -> None:
    assert await OrFilter(TrueF(), TrueF())(BaseUpdate(), Ctx({})) is True
    assert await OrFilter(TrueF(), FalseF())(BaseUpdate(), Ctx({})) is True
    assert await OrFilter(FalseF(), TrueF())(BaseUpdate(), Ctx({})) is True
    assert await OrFilter(FalseF(), FalseF())(BaseUpdate(), Ctx({})) is False


async def test_invert_filter() -> None:
    assert await InvertFilter(TrueF())(BaseUpdate(), Ctx({})) is False
    assert await InvertFilter(FalseF())(BaseUpdate(), Ctx({})) is True


async def test_and_filter_failed_chain_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await AndFilter(WritingFilter("command", "start"), FalseF())(
        BaseUpdate(),
        ctx,
    )

    assert result is False
    assert "command" not in ctx


async def test_and_filter_passed_chain_commits_ctx() -> None:
    ctx = Ctx({})

    result = await AndFilter(WritingFilter("command", "start"), TrueF())(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert ctx["command"] == "start"


async def test_and_filter_passed_chain_overwrites_existing_key() -> None:
    ctx = Ctx({"command": "old"})

    result = await AndFilter(WritingFilter("command", "new"), TrueF())(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert ctx["command"] == "new"


async def test_or_filter_failed_branch_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await OrFilter(
        WritingFilter("first", "1", result=False),
        WritingFilter("second", "2"),
    )(BaseUpdate(), ctx)

    assert result is True
    assert "first" not in ctx
    assert ctx["second"] == "2"


async def test_or_filter_all_branches_failed_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await OrFilter(
        WritingFilter("first", "1", result=False),
        WritingFilter("second", "2", result=False),
    )(BaseUpdate(), ctx)

    assert result is False
    assert "first" not in ctx
    assert "second" not in ctx


async def test_combine_filters_single_failed_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await combine_filters(WritingFilter("command", "start", result=False))(
        BaseUpdate(),
        ctx,
    )

    assert result is False
    assert "command" not in ctx


async def test_combine_filters_single_passed_commits_ctx() -> None:
    ctx = Ctx({})

    result = await combine_filters(WritingFilter("command", "start"))(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert ctx["command"] == "start"


async def test_invert_filter_failed_inner_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await InvertFilter(WritingFilter("command", "start", result=False))(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert "command" not in ctx


def test_and_inlining() -> None:
    f1 = TrueF()
    f2 = FalseF()
    f3 = TrueF()
    and_filter = AndFilter(f1, AndFilter(f2, f3))
    assert and_filter._filters == [f1, f2, f3]


def test_or_inlining() -> None:
    f1 = TrueF()
    f2 = FalseF()
    f3 = TrueF()
    or_filter = OrFilter(f1, OrFilter(f2, f3))
    assert or_filter._filters == [f1, f2, f3]


def test_invert_inlining() -> None:
    f1 = TrueF()
    inverted_filter = InvertFilter(InvertFilter(f1))
    assert inverted_filter._filter is f1
    assert inverted_filter._inlined is True


def test_combine_filters_empty_returns_always_true() -> None:
    combined: Filter[BaseUpdate] = combine_filters()
    assert isinstance(combined, AlwaysTrueFilter)


def test_combine_filters_only_none_returns_always_true() -> None:
    combined: Filter[BaseUpdate] = combine_filters(None, None)
    assert isinstance(combined, AlwaysTrueFilter)


def test_combine_filters_single_wraps_in_and_filter() -> None:
    f1 = FalseF()
    combined = combine_filters(f1)
    assert isinstance(combined, AndFilter)
    assert combined._filters == [f1]


def test_combine_filters_single_ignores_none() -> None:
    f1 = FalseF()
    combined = combine_filters(None, f1, None)
    assert isinstance(combined, AndFilter)
    assert combined._filters == [f1]


def test_combine_filters_multiple_returns_and_filter() -> None:
    f1 = TrueF()
    f2 = FalseF()
    combined = combine_filters(f1, f2)
    assert isinstance(combined, AndFilter)
    assert combined._filters == [f1, f2]


async def test_combine_filters_multiple_behaves_as_and() -> None:
    assert await combine_filters(TrueF(), TrueF())(BaseUpdate(), Ctx({})) is True
    assert await combine_filters(TrueF(), FalseF())(BaseUpdate(), Ctx({})) is False
