from collections.abc import Iterable
from itertools import chain
from typing import Any

from maxo.dialogs.api.internal import ButtonVariant, RawKeyboard
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.widgets.common import WhenCondition
from maxo.types import Callback, CallbackButton

from .base import Keyboard


class Group(Keyboard):
    def __init__(
        self,
        *buttons: Keyboard,
        id: str | None = None,
        width: int | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.buttons = buttons
        self.width = width

    def find(self, widget_id: str) -> Keyboard | None:
        widget = super().find(widget_id)
        if widget:
            return widget
        for btn in self.buttons:
            widget = btn.find(widget_id)
            if widget:
                return widget
        return None

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        kbd: RawKeyboard = []
        for b in self.buttons:
            b_kbd = await b.render_keyboard(data, manager)
            if self.width is None:
                kbd += b_kbd
            else:
                if not kbd:
                    kbd.append([])
                kbd[0].extend(chain.from_iterable(b_kbd))
        if self.width and kbd:
            kbd = self._wrap_kbd(kbd[0])
        return kbd

    def _wrap_kbd(
        self,
        kbd: Iterable[CallbackButton],
    ) -> RawKeyboard:
        res: RawKeyboard = []
        row: list[ButtonVariant] = []
        for b in kbd:
            row.append(b)
            if len(row) >= self.width:
                res.append(row)
                row = []
        if row:
            res.append(row)
        return res

    async def _process_other_callback(
        self,
        callback: Callback,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        for b in self.buttons:
            if await b.process_callback(callback, dialog, manager):
                return True
        return False


class Row(Group):
    def __init__(
        self,
        *buttons: Keyboard,
        id: str | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(
            *buttons,
            id=id,
            width=9999,
            when=when,
        )  # telegram doe not allow even 100 columns


class Column(Group):
    def __init__(
        self,
        *buttons: Keyboard,
        id: str | None = None,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(*buttons, id=id, when=when, width=1)
