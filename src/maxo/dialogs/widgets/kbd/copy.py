from typing import Any

from maxo.dialogs.api.internal import RawKeyboard, TextWidget
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.common import WhenCondition
from maxo.types import ClipboardButton

from .base import Keyboard


class CopyText(Keyboard):
    def __init__(
        self,
        text: TextWidget,
        copy_text: TextWidget,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self._text = text
        self._copy_text = copy_text

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return [
            [
                ClipboardButton(
                    text=await self._text.render_text(data, manager),
                    payload=await self._copy_text.render_text(data, manager),
                ),
            ],
        ]
