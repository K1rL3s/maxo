# ruff: noqa: PLC0415
from abc import ABC
from typing import Any, Generic, TypeVar

from maxo.routing.interfaces.filter import Filter
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class BaseFilter(ABC, Filter[_UpdateT], Generic[_UpdateT]):
    __slots__ = ()

    def __and__(self, other: "Filter[_UpdateT] | Any") -> "Filter[_UpdateT]":
        if not isinstance(other, Filter):
            return NotImplemented

        from maxo.routing.filters.logic import AndFilter

        return AndFilter(self, other)

    def __or__(self, other: "Filter[_UpdateT] | Any") -> "Filter[_UpdateT]":
        if not isinstance(other, Filter):
            return NotImplemented

        from maxo.routing.filters.logic import OrFilter

        return OrFilter(self, other)

    def __invert__(self) -> "Filter[_UpdateT]":
        from maxo.routing.filters.logic import InvertFilter

        return InvertFilter(self)

    def update_handler_flags(self, flags: dict[str, Any]) -> None:
        """Дополняет флаги хендлера при регистрации."""

    def _signature_to_string(self, *args: Any, **kwargs: Any) -> str:
        items = [repr(arg) for arg in args]
        items.extend([f"{k}={v!r}" for k, v in kwargs.items() if v is not None])

        return f"{type(self).__name__}({', '.join(items)})"
