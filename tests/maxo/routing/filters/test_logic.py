from maxo.routing.ctx import CTX_KEY, Ctx
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


class SelfRefWritingFilter(BaseFilter[BaseUpdate]):
    """Пишет в ``ctx`` через self-ссылку, а не напрямую."""

    def __init__(self, key: str, value: str, *, result: bool = True) -> None:
        self._key = key
        self._value = value
        self._result = result

    async def __call__(self, update: BaseUpdate, ctx: Ctx) -> bool:
        ctx[CTX_KEY][self._key] = self._value
        return self._result


class SelfRefProbeFilter(BaseFilter[BaseUpdate]):
    """Запоминает, на что смотрит self-ссылка внутри фильтра."""

    def __init__(self) -> None:
        self.points_to_own_ctx: bool | None = None

    async def __call__(self, update: BaseUpdate, ctx: Ctx) -> bool:
        self.points_to_own_ctx = ctx[CTX_KEY] is ctx
        return True


def self_ref_ctx() -> Ctx:
    ctx = Ctx({})
    ctx[CTX_KEY] = ctx
    return ctx


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


async def test_double_invert_behaves_as_inner_filter() -> None:
    assert await InvertFilter(InvertFilter(TrueF()))(BaseUpdate(), Ctx({})) is True
    assert await InvertFilter(InvertFilter(FalseF()))(BaseUpdate(), Ctx({})) is False


async def test_triple_invert_behaves_as_single_invert() -> None:
    triple_true = InvertFilter(InvertFilter(InvertFilter(TrueF())))
    triple_false = InvertFilter(InvertFilter(InvertFilter(FalseF())))

    assert await triple_true(BaseUpdate(), Ctx({})) is False
    assert await triple_false(BaseUpdate(), Ctx({})) is True


async def test_invert_operator_chain_keeps_parity() -> None:
    filter_ = TrueF()

    assert await (~filter_)(BaseUpdate(), Ctx({})) is False
    assert await (~~filter_)(BaseUpdate(), Ctx({})) is True
    assert await (~~~filter_)(BaseUpdate(), Ctx({})) is False
    assert await (~~~~filter_)(BaseUpdate(), Ctx({})) is True


async def test_double_invert_passed_inner_commits_ctx() -> None:
    ctx = Ctx({})

    result = await InvertFilter(InvertFilter(WritingFilter("command", "start")))(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert ctx["command"] == "start"


async def test_double_invert_failed_inner_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await InvertFilter(
        InvertFilter(WritingFilter("command", "start", result=False)),
    )(BaseUpdate(), ctx)

    assert result is False
    assert "command" not in ctx


async def test_triple_invert_failed_inner_does_not_leak_ctx() -> None:
    ctx = Ctx({})

    result = await InvertFilter(
        InvertFilter(InvertFilter(WritingFilter("command", "start", result=False))),
    )(BaseUpdate(), ctx)

    assert result is True
    assert "command" not in ctx


async def test_invert_failed_inner_does_not_leak_through_self_reference() -> None:
    ctx = self_ref_ctx()

    result = await InvertFilter(
        SelfRefWritingFilter("command", "start", result=False),
    )(BaseUpdate(), ctx)

    assert result is True
    assert "command" not in ctx


async def test_double_invert_passed_inner_commits_through_self_reference() -> None:
    ctx = self_ref_ctx()

    result = await InvertFilter(
        InvertFilter(SelfRefWritingFilter("command", "start")),
    )(BaseUpdate(), ctx)

    assert result is True
    assert ctx["command"] == "start"


async def test_self_reference_points_to_copy_inside_filter() -> None:
    ctx = self_ref_ctx()
    probe = SelfRefProbeFilter()

    assert await combine_filters(probe)(BaseUpdate(), ctx) is True
    assert probe.points_to_own_ctx is True


async def test_failed_filter_does_not_leak_through_self_reference() -> None:
    ctx = self_ref_ctx()

    result = await combine_filters(
        SelfRefWritingFilter("command", "start", result=False),
    )(BaseUpdate(), ctx)

    assert result is False
    assert "command" not in ctx


async def test_passed_filter_commits_through_self_reference() -> None:
    ctx = self_ref_ctx()

    result = await combine_filters(SelfRefWritingFilter("command", "start"))(
        BaseUpdate(),
        ctx,
    )

    assert result is True
    assert ctx["command"] == "start"


async def test_passed_filter_keeps_self_reference_intact() -> None:
    ctx = self_ref_ctx()

    assert await combine_filters(WritingFilter("command", "start"))(
        BaseUpdate(),
        ctx,
    )

    assert ctx[CTX_KEY] is ctx


async def test_ctx_without_self_reference_does_not_gain_one() -> None:
    ctx = Ctx({})

    assert await combine_filters(WritingFilter("command", "start"))(
        BaseUpdate(),
        ctx,
    )

    assert CTX_KEY not in ctx


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


def test_invert_inlining_keeps_parity() -> None:
    f1 = TrueF()
    triple_inverted = InvertFilter(InvertFilter(InvertFilter(f1)))
    assert triple_inverted._filter is f1
    assert triple_inverted._inlined is False

    quadruple_inverted = InvertFilter(triple_inverted)
    assert quadruple_inverted._filter is f1
    assert quadruple_inverted._inlined is True


async def test_repeated_inversion() -> None:
    update = BaseUpdate()
    f1: Filter[BaseUpdate] = TrueF()

    for expected in (False, True, False, True):
        f1 = InvertFilter(f1)
        assert await f1(update, Ctx({})) is expected


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
