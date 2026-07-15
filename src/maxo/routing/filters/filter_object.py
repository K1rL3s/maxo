import inspect
from typing import Any, Final, Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces.filter import Filter
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)

_RESERVED_PARAMS: Final = frozenset({"update", "ctx"})


class FilterObject(BaseFilter[_UpdateT], Generic[_UpdateT]):
    """Оборачивает фильтр и подставляет в него значения из контекста."""

    filter: Filter[_UpdateT]

    __slots__ = ("_params", "_varkw", "filter")

    def __init__(self, filter_: Filter[_UpdateT]) -> None:
        if isinstance(filter_, FilterObject):
            filter_ = filter_.filter

        self.filter = filter_
        try:
            parameters = inspect.signature(filter_).parameters.values()
        except (TypeError, ValueError):
            self._params: frozenset[str] = frozenset()
            self._varkw = False
        else:
            self._params = frozenset(
                parameter.name
                for parameter in parameters
                if parameter.kind
                in {
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                }
            ) - _RESERVED_PARAMS
            self._varkw = any(
                parameter.kind is inspect.Parameter.VAR_KEYWORD
                for parameter in parameters
            )

    def injects(self) -> bool:
        return self._varkw or bool(self._params)

    def _prepare_kwargs(self, ctx: Ctx) -> dict[str, Any]:
        if self._varkw:
            return {
                key: value for key, value in ctx.items() if key not in _RESERVED_PARAMS
            }

        return {key: ctx[key] for key in self._params if key in ctx}

    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        return await self.filter(update, ctx, **self._prepare_kwargs(ctx))


def unwrap_filter(filter_: Filter[_UpdateT]) -> Filter[_UpdateT]:
    if isinstance(filter_, FilterObject):
        return filter_.filter

    return filter_


def wrap_filter(filter_: Filter[_UpdateT]) -> Filter[_UpdateT]:
    wrapped = FilterObject(filter_)
    if wrapped.injects():
        return wrapped

    return unwrap_filter(filter_)
