from abc import ABC
from collections.abc import Callable, Coroutine, MutableSequence, Sequence
from typing import Any, ParamSpec, TypeVar, cast

from maxo.routing.ctx import Ctx
from maxo.routing.filters import AlwaysTrueFilter
from maxo.routing.interfaces import Filter, Handler, Observer
from maxo.routing.interfaces.observer import ObserverState
from maxo.routing.middlewares.manager import MiddlewareManager, MiddlewareManagerFacade
from maxo.routing.observers.state import EmptyObserverState
from maxo.routing.sentinels import UNHANDLED, SkipHandler
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ReturnT_co = TypeVar("_ReturnT_co", covariant=True)

_HandlerT = TypeVar("_HandlerT", bound=Handler[Any, Any])
_HandlerFnT = TypeVar("_HandlerFnT", bound=Callable[..., Coroutine[Any, Any, Any]])

_Params = ParamSpec("_Params")
_ReturnType = TypeVar("_ReturnType")
_HandlerFunc = Callable[[_Params], _ReturnType]


class BaseObserver(Observer[_UpdateT, _HandlerT, _HandlerFnT], ABC):
    _filter: Filter[_UpdateT]
    _handlers: MutableSequence[_HandlerT]
    _middleware: MiddlewareManagerFacade[_UpdateT]
    _state: ObserverState

    __slots__ = (
        "_filter",
        "_handlers",
        "_inner_middleware",
        "_middleware",
        "_outer_middleware",
        "_state",
    )

    def __init__(self) -> None:
        self._handlers = []
        self._filter = AlwaysTrueFilter()
        self._middleware = MiddlewareManagerFacade()
        self._state = EmptyObserverState()

    @property
    def state(self) -> ObserverState:
        return self._state

    @state.setter
    def state(self, value: ObserverState) -> None:
        self._state = value

    @property
    def handlers(self) -> Sequence[_HandlerT]:
        return self._handlers

    @property
    def middleware(self) -> MiddlewareManagerFacade[_UpdateT]:
        return self._middleware

    # Подражание aiogram,
    # чтобы по `router.message_created.outer_middleware(MyMiddleware())`
    # он добавлялся в outer-мидлвари
    @property
    def outer_middleware(self) -> MiddlewareManager[_UpdateT]:
        return self.middleware.outer

    def __call__(
        self,
        filter: Filter[_UpdateT] | None = None,
    ) -> Callable[[_HandlerFnT], _HandlerFnT]:
        def wrapper(handler_fn: _HandlerFnT) -> _HandlerFnT:
            return self.handler(handler_fn, filter)

        return wrapper

    def filter(self, filter: Filter[_UpdateT]) -> None:
        self._state.ensure_add_filter()

        self._filter = filter

    async def execute_filter(self, ctx: Ctx) -> bool:
        return await self._filter(ctx["update"], ctx)

    async def handler_lookup(self, ctx: Ctx) -> Any:
        for handler in self._handlers:
            if await handler.execute_filter(ctx):
                try:
                    return await self.execute_handler(ctx, handler)
                except SkipHandler:
                    continue

        return UNHANDLED

    async def execute_handler(
        self,
        ctx: Ctx,
        handler: _HandlerT,
    ) -> _ReturnT_co:
        chain_middlewares = self.middleware.inner.wrap_middlewares(handler)
        return cast(_ReturnT_co, await chain_middlewares(ctx))
