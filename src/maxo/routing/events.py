from typing import Generic, TypeVar

from maxo.omit import Omittable, Omitted
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ExceptionT = TypeVar("_ExceptionT", bound=Exception)


class MaxoUpdate(BaseUpdate, Generic[_UpdateT]):
    """Внутренний апдейт, используется в роутинге как обёртка над апдейтом из Макса."""

    update: _UpdateT
    marker: Omittable[int | None] = Omitted()


class ErrorEvent(BaseUpdate, Generic[_ExceptionT, _UpdateT]):
    exception: _ExceptionT
    update: MaxoUpdate[_UpdateT]

    @property
    def error(self) -> _ExceptionT:
        return self.exception

    @property
    def event(self) -> _UpdateT:
        return self.update.update
