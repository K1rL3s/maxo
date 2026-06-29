from abc import abstractmethod
from typing import Any, Protocol, TypeVar, runtime_checkable

from maxo.routing.ctx import Ctx
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


@runtime_checkable
class Filter(Protocol[_UpdateT]):
    __slots__ = ()

    @abstractmethod
    async def __call__(self, update: _UpdateT, ctx: Ctx) -> bool:
        raise NotImplementedError

    @abstractmethod
    def __and__(self, other: "Filter[_UpdateT] | Any") -> "Filter[_UpdateT]":
        raise NotImplementedError

    @abstractmethod
    def __or__(self, other: "Filter[_UpdateT] | Any") -> "Filter[_UpdateT]":
        raise NotImplementedError

    @abstractmethod
    def __invert__(self) -> "Filter[_UpdateT]":
        raise NotImplementedError
