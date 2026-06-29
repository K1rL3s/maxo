from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias, cast

from maxo.dialogs.api.internal import RawKeyboard, TextWidget
from maxo.dialogs.api.internal.middleware import PAYLOAD_KEY
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.utils import remove_intent_id
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.kbd import Keyboard
from maxo.dialogs.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)
from maxo.routing.updates import MessageCallback
from maxo.types import CallbackButton

OnClick: TypeAlias = Callable[
    [MessageCallback, "ConfirmButton", DialogManager],
    Awaitable[Any],
]

ACTION_WAIT = "__wait__"
ACTION_CONFIRM = "__confirm__"
ACTION_CANCEL = "__cancel__"


class ConfirmButton(Keyboard):
    def __init__(
        self,
        id: str,
        primary_text: TextWidget,
        confirm_text: TextWidget,
        cancel_text: TextWidget,
        warning_text: TextWidget | None = None,
        on_confirm: OnClick | WidgetEventProcessor | None = None,
        on_cancel: OnClick | WidgetEventProcessor | None = None,
        confirm_first: bool = False,
        oneline: bool = True,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.primary_text = primary_text
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.warning_text = warning_text
        self.on_confirm = ensure_event_processor(on_confirm)
        self.on_cancel = ensure_event_processor(on_cancel)
        self.confirm_first = confirm_first
        self.oneline = oneline

    async def _process_item_callback(
        self,
        callback: MessageCallback,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        if data == ACTION_CONFIRM:
            await self.on_confirm.process_event(callback, self, manager)
        elif data == ACTION_CANCEL:
            await self.on_cancel.process_event(callback, self, manager)
        return True

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        payload: str | None = manager.middleware_data.get(PAYLOAD_KEY)
        action = self._get_action(payload)

        # Шаг подтверждения: warning + cancel/confirm
        if action == ACTION_WAIT:
            keyboard = []
            if self.warning_text is not None:
                keyboard.append(
                    [
                        CallbackButton(
                            text=await self.warning_text.render_text(data, manager),
                            payload=self._item_payload(ACTION_WAIT),
                        ),
                    ],
                )
            cancel = CallbackButton(
                text=await self.cancel_text.render_text(data, manager),
                payload=self._item_payload(ACTION_CANCEL),
            )
            confirm = CallbackButton(
                text=await self.confirm_text.render_text(data, manager),
                payload=self._item_payload(ACTION_CONFIRM),
            )

            if self.oneline:
                if self.confirm_first:
                    keyboard.append([confirm, cancel])
                else:
                    keyboard.append([cancel, confirm])
            elif self.confirm_first:
                keyboard.append([confirm])
                keyboard.append([cancel])
            else:
                keyboard.append([cancel])
                keyboard.append([confirm])

            return cast(RawKeyboard, keyboard)

        # Любая другая кнопка, из другого окна или cancel/confirm
        return [
            [
                CallbackButton(
                    text=await self.primary_text.render_text(data, manager),
                    payload=self._item_payload(ACTION_WAIT),
                ),
            ],
        ]

    def _get_action(self, payload: str | None) -> str | None:
        if payload is None:
            return None

        # убрать intent, потому что в _render_keyboard попадает что угодно
        _, payload = remove_intent_id(payload)

        # проверка что кнопка относится к этому виджету
        prefix = self.callback_prefix()
        if not prefix or not payload.startswith(prefix):
            return None

        # ищем action (__confirm__ итп)
        return payload[len(prefix) :]
