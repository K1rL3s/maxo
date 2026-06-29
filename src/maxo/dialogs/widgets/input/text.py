from abc import abstractmethod
from collections.abc import Callable
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
)

from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.widgets.common import ManagedWidget
from maxo.dialogs.widgets.filter_object import FilterObject
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.routing.updates import MessageCreated

from .base import BaseInput

T = TypeVar("T")
TypeFactory = Callable[[str], T]


class OnSuccess(Protocol[T]):
    @abstractmethod
    async def __call__(
        self,
        message: MessageCreated,
        widget: "ManagedTextInput[T]",
        dialog_manager: DialogManager,
        data: T,
        /,
    ) -> None:
        raise NotImplementedError


class OnError(Protocol[T]):
    @abstractmethod
    async def __call__(
        self,
        message: MessageCreated,
        widget: "ManagedTextInput[T]",
        dialog_manager: DialogManager,
        error: ValueError,
        /,
    ) -> None:
        raise NotImplementedError


class TextInput(BaseInput, Generic[T]):
    def __init__(
        self,
        id: str,
        type_factory: TypeFactory[T] = str,
        on_success: OnSuccess[T] | WidgetEventProcessor | None = None,
        on_error: OnError | WidgetEventProcessor | None = None,
        filter: Callable[..., Any] | None = None,
    ) -> None:
        super().__init__(id=id)
        if filter is not None:
            self.filter = FilterObject(filter)
        else:
            self.filter = None
        self.type_factory = type_factory
        self.on_success = ensure_event_processor(on_success)
        self.on_error = ensure_event_processor(on_error)

    async def process_message(
        self,
        message: MessageCreated,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        if message.message.body is None:
            return False
        if not message.message.body.text:
            return False

        if self.filter and not await self.filter.call(
            manager.event,
            **manager.middleware_data,
        ):
            return False
        try:
            value = self.type_factory(message.message.body.text)
        except ValueError as err:
            await self.on_error.process_event(
                message,
                self.managed(manager),
                manager,
                err,
            )
        else:
            # store original text
            self.set_widget_data(manager, message.message.body.text)
            await self.on_success.process_event(
                message,
                self.managed(manager),
                manager,
                value,
            )
        return True

    def get_value(self, manager: DialogManager) -> T | None:
        data = self.get_widget_data(manager, None)
        if data is None:
            return None
        return self.type_factory(data)

    def managed(self, manager: DialogManager) -> "ManagedTextInput[T]":
        return ManagedTextInput(self, manager)


class ManagedTextInput(ManagedWidget[TextInput[T]], Generic[T]):
    def get_value(self) -> T | None:
        """Get last input data stored by widget."""
        return self.widget.get_value(self.manager)
