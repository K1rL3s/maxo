from abc import abstractmethod
from collections.abc import Callable, Coroutine, Sequence
from typing import Any, Protocol, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.filter import Filter
from maxo.routing.interfaces.handler import Handler
from maxo.routing.middlewares.manager import MiddlewareManagerFacade
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ReturnT_co = TypeVar("_ReturnT_co", covariant=True)

_HandlerT = TypeVar("_HandlerT", bound=Handler[Any, Any])
_HandlerFnT = TypeVar("_HandlerFnT", bound=Callable[..., Coroutine[Any, Any, Any]])


class ObserverState(Protocol):
    @abstractmethod
    def ensure_add_handler(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_add_filter(self) -> None:
        raise NotImplementedError


class Observer(Protocol[_UpdateT, _HandlerT, _HandlerFnT]):
    __slots__ = ()

    @property
    @abstractmethod
    def state(self) -> ObserverState:
        raise NotImplementedError

    @state.setter
    @abstractmethod
    def state(self, value: ObserverState) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def handlers(self) -> Sequence[_HandlerT]:
        raise NotImplementedError

    @property
    @abstractmethod
    def middleware(self) -> MiddlewareManagerFacade[_UpdateT]:
        raise NotImplementedError

    @abstractmethod
    def __call__(
        self,
        filter: Filter[_UpdateT] | None = None,
    ) -> Callable[[_HandlerFnT], _HandlerFnT]:
        raise NotImplementedError

    @abstractmethod
    def handler(
        self,
        handler_fn: _HandlerFnT,
        filter: Filter[_UpdateT] | None = None,
    ) -> _HandlerFnT:
        raise NotImplementedError

    # Подражание aiogram
    def register(
        self,
        handler_fn: _HandlerFnT,
        filter: Filter[_UpdateT] | None = None,
    ) -> _HandlerFnT:
        return self.handler(handler_fn, filter)

    @abstractmethod
    def filter(self, filter: Filter[_UpdateT]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def execute_filter(self, ctx: Ctx) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def handler_lookup(self, ctx: Ctx) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def execute_handler(self, ctx: Ctx, handler: _HandlerT) -> _ReturnT_co:
        raise NotImplementedError
