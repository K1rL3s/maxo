from maxo.routing.ctx import Ctx
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter
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


async def test_invert_inlining() -> None:
    f1 = TrueF()

    assert await InvertFilter(InvertFilter(f1))(BaseUpdate(), Ctx({})) is True
    assert await InvertFilter(InvertFilter(InvertFilter(f1)))(BaseUpdate(), Ctx({})) is False


def test_combine_filters_empty_returns_always_true() -> None:
    combined: Filter[BaseUpdate] = combine_filters()
    assert isinstance(combined, AlwaysTrueFilter)


def test_combine_filters_only_none_returns_always_true() -> None:
    combined: Filter[BaseUpdate] = combine_filters(None, None)
    assert isinstance(combined, AlwaysTrueFilter)


def test_combine_filters_single_returns_same_filter() -> None:
    f1 = FalseF()
    assert combine_filters(f1) is f1


def test_combine_filters_single_ignores_none() -> None:
    f1 = FalseF()
    assert combine_filters(None, f1, None) is f1


def test_combine_filters_multiple_returns_and_filter() -> None:
    f1 = TrueF()
    f2 = FalseF()
    combined = combine_filters(f1, f2)
    assert isinstance(combined, AndFilter)
    assert combined._filters == [f1, f2]


async def test_combine_filters_multiple_behaves_as_and() -> None:
    assert await combine_filters(TrueF(), TrueF())(BaseUpdate(), Ctx({})) is True
    assert await combine_filters(TrueF(), FalseF())(BaseUpdate(), Ctx({})) is False
