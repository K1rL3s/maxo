from typing import Any

from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.common import WhenCondition

from .base import Text


class Progress(Text):
    def __init__(
        self,
        field: str,
        width: int = 10,
        filled: str = "🟥",
        empty: str = "⬜",
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when)
        self.field = field
        self.width = width
        self.filled = filled
        self.empty = empty

    async def _render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        raw_percent = 15 if manager.is_preview() else data.get(self.field, 0)
        percent = float(raw_percent)
        done = round((self.width * percent) / 100)
        rest = self.width - done

        return self.filled * done + self.empty * rest + f" {percent: 2.0f}%"
