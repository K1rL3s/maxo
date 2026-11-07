from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.handlers.update import UpdateHandler, UpdateHandlerFn
from maxo.routing.interfaces.filter import Filter
from maxo.routing.observers.base import BaseObserver
from maxo.types.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ReturnT_co = TypeVar("_ReturnT_co", covariant=True)


class UpdateObserver(
    BaseObserver[
        _UpdateT,
        UpdateHandler[_UpdateT, Any],
        UpdateHandlerFn[_UpdateT, Any],
    ],
    Generic[_UpdateT],
):
    def handler(
        self,
        handler_fn: UpdateHandlerFn[_UpdateT, Any],
        *filters: Filter[_UpdateT],
        flags: Mapping[str, Any] | None = None,
    ) -> UpdateHandlerFn[_UpdateT, Any]:
        self.state.ensure_add_handler()

        self._handlers.append(UpdateHandler(handler_fn, *filters, flags=flags))

        return handler_fn

    register = handler  # Подражание aiogram

    if TYPE_CHECKING:

        async def execute_handler(
            self,
            ctx: Ctx,
            handler: UpdateHandler[_UpdateT, _ReturnT_co],
        ) -> _ReturnT_co: ...
