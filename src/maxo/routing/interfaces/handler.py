from abc import abstractmethod
from typing import Any, Protocol, TypeVar

from maxo.routing.ctx import Ctx
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ReturnT_co = TypeVar("_ReturnT_co", covariant=True)


class Handler(Protocol[_UpdateT, _ReturnT_co]):  # type: ignore[misc]
    __slots__ = ()

    @property
    @abstractmethod
    def flags(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def execute_filter(self, ctx: Ctx) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def __call__(self, ctx: Ctx) -> _ReturnT_co:
        raise NotImplementedError
