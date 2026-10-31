from abc import abstractmethod
from collections.abc import MutableMapping, Sequence
from typing import Any, Protocol

from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.observer import Observer


class BaseRouter(Protocol):
    __slots__ = ()

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

    @property
    @abstractmethod
    def parent_router(self) -> "BaseRouter | None":
        raise NotImplementedError

    @parent_router.setter
    @abstractmethod
    def parent_router(self, value: "BaseRouter | None") -> None:
        raise NotImplementedError
