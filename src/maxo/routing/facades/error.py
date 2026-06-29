from typing import Generic, TypeVar

from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.signals import MaxoUpdate
from maxo.routing.updates.base import BaseUpdate
from maxo.routing.updates.error import ErrorEvent

_ExceptionT = TypeVar("_ExceptionT", bound=Exception)
_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class ErrorEventFacade(
    BaseUpdateFacade[ErrorEvent[_ExceptionT, _UpdateT]],
    Generic[_ExceptionT, _UpdateT],
):
    @property
    def exception(self) -> _ExceptionT:
        return self._update.exception

    @property
    def update(self) -> MaxoUpdate[_UpdateT]:
        return self._update.update

    @property
    def error(self) -> _ExceptionT:
        return self._update.error

    @property
    def event(self) -> _UpdateT:
        return self._update.event
