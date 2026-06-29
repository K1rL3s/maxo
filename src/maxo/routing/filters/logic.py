# ruff: noqa: SLF001

from abc import abstractmethod
from collections.abc import Sequence
from copy import copy
from typing import Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class BaseLogicFilter(BaseFilter[_UpdateT], Generic[_UpdateT]):
    __slots__ = ()

    def __init__(self) -> None:
        self._inlining()

    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        copied_ctx = copy(ctx)

        reduce_result = await self._reduce(update, ctx)
        if reduce_result:
            ctx.update(copied_ctx)

        return reduce_result

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
            loop_copied_ctx = copy(ctx)

            filter_result = await filter_(update, loop_copied_ctx)
            if not filter_result:
                return False

            ctx.update(loop_copied_ctx)

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
            loop_copied_ctx = copy(ctx)

            filter_result = await filter_(update, loop_copied_ctx)
            if filter_result:
                ctx.update(loop_copied_ctx)
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
        filter_result = await self._filter(update, ctx)
        if self._inlined:
            return filter_result
        return not filter_result

    def _inlining(self) -> None:
        if isinstance(self._filter, InvertFilter):
            self._filter = self._filter._filter
            self._inlined = True
        else:
            self._inlined = False


and_f = AndFilter
or_f = OrFilter
invert_f = InvertFilter
