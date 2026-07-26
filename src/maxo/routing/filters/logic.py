# ruff: noqa: SLF001

from abc import abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from copy import copy
from typing import Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.always import AlwaysTrueFilter
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class BaseLogicFilter(BaseFilter[_UpdateT], Generic[_UpdateT]):
    __slots__ = ()

    def __init__(self) -> None:
        self._inlining()

    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        return await _run_isolated(self._reduce, update, ctx)

    @abstractmethod
    async def _reduce(self, update: _UpdateT, ctx: Ctx) -> bool:
        raise NotImplementedError

    @abstractmethod
    def _inlining(self) -> None:
        raise NotImplementedError


class AndFilter(BaseLogicFilter[_UpdateT], Generic[_UpdateT]):
    _filters: Sequence[Filter[_UpdateT]]

    def __init__(self, *filters: Filter[_UpdateT]) -> None:
        self._filters = filters
        super().__init__()

    async def _reduce(self, update: _UpdateT, ctx: Ctx) -> bool:
        for filter_ in self._filters:
            if not await filter_(update, ctx):
                return False

        return True

    def _inlining(self) -> None:
        inlined_filters: list[Filter[_UpdateT]] = []

        for filter in self._filters:
            if isinstance(filter, AndFilter):
                inlined_filters.extend(filter._filters)
            else:
                inlined_filters.append(filter)

        self._filters = inlined_filters


class OrFilter(BaseLogicFilter[_UpdateT], Generic[_UpdateT]):
    _filters: Sequence[Filter[_UpdateT]]

    def __init__(
        self,
        *filters: Filter[_UpdateT],
    ) -> None:
        self._filters = filters
        super().__init__()

    async def _reduce(self, update: _UpdateT, ctx: Ctx) -> bool:
        for filter_ in self._filters:
            if await _run_isolated(filter_, update, ctx):
                return True

        return False

    def _inlining(self) -> None:
        inlined_filters: list[Filter[_UpdateT]] = []

        for filter in self._filters:
            if isinstance(filter, OrFilter):
                inlined_filters.extend(filter._filters)
            else:
                inlined_filters.append(filter)

        self._filters = inlined_filters


class InvertFilter(BaseLogicFilter[_UpdateT], Generic[_UpdateT]):
    _inlined: bool

    def __init__(
        self,
        filter_: Filter[_UpdateT],
    ) -> None:
        self._filter = filter_
        super().__init__()

    async def _reduce(self, update: _UpdateT, ctx: Ctx) -> bool:
        if self._inlined:
            return await self._filter(update, ctx)
        return not await self._filter(update, copy(ctx))

    def _inlining(self) -> None:
        inner = self._filter
        if isinstance(inner, InvertFilter):
            # `~~f` эквивалентно `f`, поэтому цепочка инверсий схлопывается в
            # один узел. Чётность считаем по вложенному фильтру: если он сам уже
            # схлопнут в тождество (`_inlined is True`), то текущая инверсия
            # снова становится настоящей.
            self._inlined = not inner._inlined
            self._filter = inner._filter
        else:
            self._inlined = False


and_f = AndFilter
or_f = OrFilter
invert_f = InvertFilter


def combine_filters(*filters: Filter[_UpdateT] | None) -> Filter[_UpdateT]:
    """
    Склеивает фильтры в один фильтр по правилу `И`.

    Даже единственный фильтр оборачивается в ``AndFilter``, чтобы его записи в
    ``ctx`` проходили ту же изоляцию: они попадают в общий ``ctx`` только если
    фильтр прошёл.
    """
    real_filters = [filter_ for filter_ in filters if filter_ is not None]
    if not real_filters:
        return AlwaysTrueFilter()
    return AndFilter(*real_filters)


async def _run_isolated(
    filter_: Callable[[_UpdateT, Ctx], Awaitable[bool]],
    update: _UpdateT,
    ctx: Ctx,
) -> bool:
    """
    Прогоняет фильтр на копии ``ctx``.

    Записи фильтра попадают в общий ``ctx`` только если он вернул ``True``.
    Если фильтр не прошёл, его изменения отбрасываются и не видны никому дальше.
    """
    copied_ctx = copy(ctx)
    if await filter_(update, copied_ctx):
        ctx.update(copied_ctx)
        return True
    return False
