from typing import Any

from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.widgets.common import WhenCondition

from .base import Text


class _FormatDataStub:
    def __init__(self, name: str = "", data: dict[Any, Any] | None = None) -> None:
        self.name = name
        self.data = data or {}

    def __getitem__(self, item: Any) -> "_FormatDataStub":
        if item in self.data:
            return self.data[item]
        if not self.name:
            return _FormatDataStub(item)
        return _FormatDataStub(f"{self.name}[{item}]")

    def __getattr__(self, item: Any) -> "_FormatDataStub":
        return _FormatDataStub(f"{self.name}.{item}")

    def __format__(self, format_spec: str) -> str:
        res = f"{self.name}:{format_spec}" if format_spec else self.name
        return f"{{{res}}}"


class Format(Text):
    def __init__(self, text: str, when: WhenCondition = None) -> None:
        super().__init__(when=when)
        self.text = text

    async def _render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        if manager.is_preview():
            return self.text.format_map(_FormatDataStub(data=data))
        return self.text.format_map(data)
