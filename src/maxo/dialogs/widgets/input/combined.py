from collections.abc import Callable
from typing import Any

from maxo.dialogs.api.protocols import (
    DialogManager,
    DialogProtocol,
)
from maxo.dialogs.widgets.filter_object import FilterObject
from maxo.routing.updates import MessageCreated

from .base import BaseInput


class CombinedInput(BaseInput):
    def __init__(
        self,
        *inputs: BaseInput,
        filter: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__()
        self.inputs = inputs
        self.filters = []
        if filter is not None:
            self.filters.append(FilterObject(filter))

    async def process_message(
        self,
        message: MessageCreated,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        for handler_filter in self.filters:
            if not await handler_filter.call(
                manager.event,
                **manager.middleware_data,
            ):
                return False
        for input_widget in self.inputs:
            if await input_widget.process_message(message, dialog, manager):
                return True
        return False
