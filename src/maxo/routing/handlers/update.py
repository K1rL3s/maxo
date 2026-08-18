import asyncio
import inspect
from collections.abc import Mapping
from functools import partial
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from maxo.routing.ctx import Ctx
from maxo.routing.filters.logic import combine_filters
from maxo.routing.flags import resolve_handler_flags
from maxo.routing.interfaces.filter import Filter
from maxo.routing.interfaces.handler import Handler
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ReturnT_co = TypeVar("_ReturnT_co", covariant=True)


@runtime_checkable
class UpdateHandlerFn(Protocol[_UpdateT, _ReturnT_co]):  # type: ignore[misc]
    async def __call__(
        self,
        update: _UpdateT,
        /,
        *args: Any,
        **kwargs: Any,
    ) -> _ReturnT_co: ...


class UpdateHandler(
    Handler[_UpdateT, _ReturnT_co],
    Generic[_UpdateT, _ReturnT_co],
):
    __slots__ = (
        "_awaitable",
        "_filter",
        "_flags",
        "_handler_fn",
        "_params",
        "_varkw",
    )

    def __init__(
        self,
        handler_fn: UpdateHandlerFn[_UpdateT, _ReturnT_co],
        *filters: Filter[_UpdateT],
        flags: Mapping[str, Any] | None = None,
    ) -> None:
        self._filter = combine_filters(*filters)
        self._handler_fn = handler_fn
        self._flags = resolve_handler_flags(handler_fn, filters, flags)
        self._awaitable = inspect.isawaitable(
            handler_fn,
        ) or inspect.iscoroutinefunction(handler_fn)
        spec = inspect.getfullargspec(handler_fn)
        self._params = {*spec.args, *spec.kwonlyargs}
        self._varkw = spec.varkw is not None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(handler_fn={self._handler_fn}, filter={self._filter})"
        )

    @property
    def flags(self) -> dict[str, Any]:
        self._flags.update(resolve_handler_flags(self._handler_fn))
        return self._flags

    def _prepare_kwargs(self, ctx: Ctx) -> dict[str, Any]:
        if self._varkw:
            return dict(ctx)

        return {k: ctx[k] for k in self._params if k in ctx}

    async def execute_filter(self, ctx: Ctx) -> bool:
        return await self._filter(ctx["update"], ctx)

    async def __call__(self, ctx: Ctx) -> _ReturnT_co:
        # потому что update это первый аргумент в хендлерах
        update = ctx.pop("update")
        wrapped = partial(self._handler_fn, update, **self._prepare_kwargs(ctx))
        ctx["update"] = update
        if self._awaitable:
            return await wrapped()
        # В этой ветке хендлер синхронный, несмотря на async-сигнатуру протокола.
        return await asyncio.to_thread(wrapped)  # type: ignore[arg-type]
