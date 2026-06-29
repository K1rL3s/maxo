import pytest

from maxo import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.filters.logic import AndFilter, InvertFilter, OrFilter
from maxo.routing.updates.base import BaseUpdate


class MyTestFilter(BaseFilter):
    async def __call__(self, update: BaseUpdate, ctx: Ctx) -> bool:
        return True


def test_filter_and():
    f1 = MyTestFilter()
    f2 = MyTestFilter()
    and_filter = f1 & f2
    assert isinstance(and_filter, AndFilter)
    assert and_filter._filters == [f1, f2]


def test_filter_or():
    f1 = MyTestFilter()
    f2 = MyTestFilter()
    or_filter = f1 | f2
    assert isinstance(or_filter, OrFilter)
    assert or_filter._filters == [f1, f2]


def test_filter_invert():
    f1 = MyTestFilter()
    inverted_filter = ~f1
    assert isinstance(inverted_filter, InvertFilter)
    assert inverted_filter._filter is f1


def test_filter_and_not_filter():
    f1 = MyTestFilter()
    with pytest.raises(TypeError):
        f1 & "not a filter"


def test_filter_or_not_filter():
    f1 = MyTestFilter()
    with pytest.raises(TypeError):
        f1 | "not a filter"


def test_signature_to_string():
    f1 = MyTestFilter()
    assert (
        f1._signature_to_string(1, "a", key="value")
        == "MyTestFilter(1, 'a', key='value')"
    )
