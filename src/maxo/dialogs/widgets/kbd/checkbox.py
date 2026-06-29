from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.api.internal import RawKeyboard, TextWidget
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.widgets.common import ManagedWidget, WhenCondition
from maxo.dialogs.widgets.text import Case
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.types import Callback, CallbackButton

from .base import Keyboard

OnStateChanged = Callable[
    [ChatEvent, "ManagedCheckbox", DialogManager],
    Awaitable,
]
OnStateChangedVariant = OnStateChanged | WidgetEventProcessor | None


class BaseCheckbox(Keyboard, ABC):
    def __init__(
        self,
        checked_text: TextWidget,
        unchecked_text: TextWidget,
        id: str,
        on_click: OnStateChangedVariant = None,
        on_state_changed: OnStateChangedVariant = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.text = Case(
            {True: checked_text, False: unchecked_text},
            selector=self._is_text_checked,
        )
        self.on_click = ensure_event_processor(on_click)
        self.on_state_changed = ensure_event_processor(on_state_changed)

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        checked = int(self.is_checked(manager))
        # store current checked status in callback data
        return [
            [
                CallbackButton(
                    text=await self.text.render_text(data, manager),
                    payload=self._item_payload(checked),
                ),
            ],
        ]

    async def _process_item_callback(
        self,
        callback: Callback,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        # remove prefix and cast "0" as False, "1" as True
        checked = data != "0"
        await self.on_click.process_event(
            callback,
            self.managed(manager),
            manager,
        )
        await self.set_checked(callback, not checked, manager)
        return True

    def _is_text_checked(
        self,
        data: dict[Any, Any],
        case: Case,
        manager: DialogManager,
    ) -> bool:
        del data  # unused
        del case  # unused
        return self.is_checked(manager)

    @abstractmethod
    def is_checked(self, manager: DialogManager) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def set_checked(
        self,
        event: ChatEvent,
        checked: bool,
        manager: DialogManager,
    ) -> None:
        raise NotImplementedError


class Checkbox(BaseCheckbox):
    def __init__(
        self,
        checked_text: TextWidget,
        unchecked_text: TextWidget,
        id: str,
        on_click: OnStateChanged | WidgetEventProcessor | None = None,
        on_state_changed: OnStateChanged | None = None,
        default: bool = False,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(
            checked_text=checked_text,
            unchecked_text=unchecked_text,
            on_click=on_click,
            on_state_changed=on_state_changed,
            id=id,
            when=when,
        )
        self.default = default

    def is_checked(self, manager: DialogManager) -> bool:
        return self.get_widget_data(manager, self.default)

    async def set_checked(
        self,
        event: ChatEvent,
        checked: bool,
        manager: DialogManager,
    ) -> None:
        self.set_widget_data(manager, checked)
        await self.on_state_changed.process_event(
            event,
            self.managed(manager),
            manager,
        )

    def managed(self, manager: DialogManager) -> "ManagedCheckbox":
        return ManagedCheckbox(self, manager)


class ManagedCheckbox(ManagedWidget[Checkbox]):
    def is_checked(self) -> bool:
        return self.widget.is_checked(self.manager)

    async def set_checked(self, checked: bool) -> None:
        await self.widget.set_checked(
            self.manager.event,
            checked,
            self.manager,
        )
