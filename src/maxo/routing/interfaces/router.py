from abc import abstractmethod
from collections.abc import MutableMapping, Sequence
from typing import Any, Protocol

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.observer import Observer


class RouterState(Protocol):
    @abstractmethod
    def ensure_include(self) -> None:
        raise NotImplementedError


class BaseRouter(Protocol):
    __slots__ = ()

    @property
    @abstractmethod
    def state(self) -> RouterState:
        raise NotImplementedError

    @state.setter
    @abstractmethod
    def state(self, value: RouterState) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def observers(self) -> MutableMapping[Any, Observer[Any, Any, Any]]:
        raise NotImplementedError

    @property
    @abstractmethod
    def children_routers(self) -> Sequence["BaseRouter"]:
        raise NotImplementedError

    @abstractmethod
    def include(self, *routers: "BaseRouter") -> None:
        raise NotImplementedError

    # Подражание aiogram
    def include_router(self, router: "BaseRouter") -> None:
        return self.include(router)

    # Подражание aiogram
    def include_routers(self, *routers: "BaseRouter") -> None:
        return self.include(*routers)

    @abstractmethod
    async def trigger_child(self, ctx: Ctx) -> Any:
        raise NotImplementedError

    @abstractmethod
    async def trigger(self, ctx: Ctx) -> Any:
        raise NotImplementedError
