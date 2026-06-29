from abc import abstractmethod
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from maxo import Ctx
from maxo.dialogs.api.internal import InputWidget
from maxo.dialogs.api.protocols import (
    DialogManager,
    DialogProtocol,
)
from maxo.dialogs.widgets.common import Actionable
from maxo.dialogs.widgets.filter_object import FilterObject
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.enums import AttachmentType
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCreated

MessageHandlerFunc = Callable[
    [MessageCreated, "MessageInput", DialogManager],
    Awaitable,
]


class BaseInput(Actionable, InputWidget):
    @abstractmethod
    async def process_message(
        self,
        message: MessageCreated,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        raise NotImplementedError


class MessageInput(BaseInput):
    def __init__(
        self,
        func: MessageHandlerFunc | WidgetEventProcessor | None,
        content_types: Sequence[AttachmentType] | AttachmentType | None = None,
        filter: Callable[..., Any] | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self.func = ensure_event_processor(func)

        filters = []
        if content_types is not None:
            if isinstance(content_types, str):
                content_types = [content_types]
            filters.append(FilterObject(ContentTypeFilter(content_types)))
        if filter is not None:
            filters.append(FilterObject(filter))
        self.filters = filters

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
        await self.func.process_event(message, self, manager)
        return True


class ContentTypeFilter(BaseFilter[MessageCreated]):
    def __init__(self, content_types: Sequence[AttachmentType]) -> None:
        self._content_types = content_types

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        if AttachmentType.TEXT in self._content_types and update.message.body.text:
            return True

        for attach in update.message.body.attachments or []:
            if attach.type in self._content_types:
                return True

        return False
