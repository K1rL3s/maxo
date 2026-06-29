from typing import Any

from maxo.dialogs.api.entities import ChatEvent, Data, ShowMode, StartMode
from maxo.dialogs.api.internal import TextWidget
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.kbd.button import Button, OnClick
from maxo.dialogs.widgets.text import Const
from maxo.dialogs.widgets.widget_event import WidgetEventProcessor
from maxo.fsm import State
from maxo.routing.updates import MessageCallback

BACK_TEXT = Const("Back")
NEXT_TEXT = Const("Next")
CANCEL_TEXT = Const("Cancel")


class EventProcessorButton(Button, WidgetEventProcessor):
    async def process_event(
        self,
        event: ChatEvent,
        source: Any,
        manager: DialogManager,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        await self._on_click(event, self, manager)

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        raise NotImplementedError


class SwitchTo(EventProcessorButton):
    def __init__(
        self,
        text: TextWidget,
        id: str,
        state: State,
        on_click: OnClick | None = None,
        when: WhenCondition = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        super().__init__(
            text=text,
            on_click=self._on_click,
            id=id,
            when=when,
        )
        self.text = text
        self.user_on_click = on_click
        self.state = state
        self.show_mode = show_mode

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)
        await manager.switch_to(self.state, show_mode=self.show_mode)


class Next(EventProcessorButton):
    def __init__(
        self,
        text: TextWidget = NEXT_TEXT,
        id: str = "__next__",
        on_click: OnClick | None = None,
        show_mode: ShowMode | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(
            text=text,
            on_click=self._on_click,
            id=id,
            when=when,
        )
        self.text = text
        self.show_mode = show_mode
        self.user_on_click = on_click

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)
        await manager.next(self.show_mode)


class Back(EventProcessorButton):
    def __init__(
        self,
        text: TextWidget = BACK_TEXT,
        id: str = "__back__",
        on_click: OnClick | None = None,
        show_mode: ShowMode | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(
            text=text,
            on_click=self._on_click,
            id=id,
            when=when,
        )
        self.text = text
        self.payload = id
        self.show_mode = show_mode
        self.user_on_click = on_click

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)
        await manager.back(self.show_mode)


class Cancel(EventProcessorButton):
    def __init__(
        self,
        text: TextWidget = CANCEL_TEXT,
        id: str = "__cancel__",
        result: Any = None,
        on_click: OnClick | None = None,
        when: WhenCondition = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        super().__init__(
            text=text,
            on_click=self._on_click,
            id=id,
            when=when,
        )
        self.text = text
        self.result = result
        self.user_on_click = on_click
        self.show_mode = show_mode

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)
        await manager.done(self.result, show_mode=self.show_mode)


class Start(EventProcessorButton):
    def __init__(
        self,
        text: TextWidget,
        id: str,
        state: State,
        data: Data = None,
        on_click: OnClick | None = None,
        show_mode: ShowMode | None = None,
        mode: StartMode = StartMode.NORMAL,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(
            text=text,
            on_click=self._on_click,
            id=id,
            when=when,
        )
        self.text = text
        self.start_data = data
        self.user_on_click = on_click
        self.show_mode = show_mode
        self.state = state
        self.mode = mode

    async def _on_click(
        self,
        callback: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        if self.user_on_click:
            await self.user_on_click(callback, self, manager)
        await manager.start(
            state=self.state,
            data=self.start_data,
            mode=self.mode,
            show_mode=self.show_mode,
        )
