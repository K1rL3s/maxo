from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

from maxo.dialogs.api.internal import RawKeyboard, TextWidget
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.omit import Omittable, Omitted
from maxo.routing.updates import MessageCallback
from maxo.types import CallbackButton, ClipboardButton, LinkButton, OpenAppButton

from .base import Keyboard

OnClick: TypeAlias = Callable[
    [MessageCallback, "Button", DialogManager],
    Awaitable[Any],
]


class Button(Keyboard):
    def __init__(
        self,
        text: TextWidget,
        id: str,
        on_click: OnClick | WidgetEventProcessor | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.text = text
        self.on_click = ensure_event_processor(on_click)

    async def _process_own_callback(
        self,
        callback: MessageCallback,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await self.on_click.process_event(callback, self, manager)
        return True

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return [
            [
                CallbackButton(
                    text=await self.text.render_text(data, manager),
                    payload=self._own_payload(),
                ),
            ],
        ]


class Url(Keyboard):
    def __init__(
        self,
        text: TextWidget,
        url: TextWidget,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.text = text
        self.url = url

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return [
            [
                LinkButton(
                    text=await self.text.render_text(data, manager),
                    url=await self.url.render_text(data, manager),
                ),
            ],
        ]


Link = Url


class WebApp(Keyboard):
    def __init__(
        self,
        text: TextWidget,
        web_app: TextWidget,
        contact_id: Omittable[int] = Omitted(),
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.text = text
        self.web_app = web_app
        self.contact_id = contact_id

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        text = await self.text.render_text(data, manager)
        web_app = await self.web_app.render_text(data, manager)

        return [
            [
                OpenAppButton(
                    text=text,
                    web_app=web_app,
                    contact_id=self.contact_id,
                ),
            ],
        ]


class Clipboard(Keyboard):
    def __init__(
        self,
        text: TextWidget,
        payload: TextWidget,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.text = text
        self.payload = payload

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return [
            [
                ClipboardButton(
                    text=await self.text.render_text(data, manager),
                    payload=await self.payload.render_text(data, manager),
                ),
            ],
        ]
