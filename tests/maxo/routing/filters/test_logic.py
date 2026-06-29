from maxo.routing.ctx import Ctx
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter
from maxo.routing.filters.logic import AndFilter, InvertFilter, OrFilter
from maxo.routing.updates.base import BaseUpdate

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


def test_invert_inlining() -> None:
    f1 = TrueF()
    inverted_filter = InvertFilter(InvertFilter(f1))
    assert inverted_filter._filter is f1
    assert inverted_filter._inlined is True
