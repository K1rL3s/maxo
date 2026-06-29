from abc import abstractmethod
from typing import Any, Optional, Self, Union, cast

from maxo.dialogs.api.internal import TextWidget
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.utils import add_exception_note
from maxo.dialogs.widgets.common import (
    BaseWidget,
    WhenCondition,
    Whenable,
    true_condition,
)


class Text(Whenable, BaseWidget, TextWidget):
    def __init__(self, when: WhenCondition = None) -> None:
        super().__init__(when=when)

    @add_exception_note
    async def render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        """
        Create text.

        When inheriting override `_render_text` method instead
        if you want to keep processing of `when` condition
        """
        if not self.is_(data, manager):
            return ""
        return await self._render_text(data, manager)

    @abstractmethod
    async def _render_text(self, data: dict[Any, Any], manager: DialogManager) -> str:
        """
        Create text.

        Called if widget is not hidden only (regarding `when`-condition)
        """
        raise NotImplementedError

    def __add__(self, other: Union["Text", str]) -> "Multi":
        if isinstance(other, str):
            other = Const(other)
        elif isinstance(other, Multi):
            return NotImplemented
        return Multi(self, other, sep="")

    def __radd__(self, other: Union["Text", str]) -> "Multi":
        if isinstance(other, str):
            other = Const(other)
        return Multi(other, self, sep="")

    def __or__(self, other: Union["Text", str]) -> "Or":
        if isinstance(other, str):
            other = Const(other)
        elif isinstance(other, Or):
            return NotImplemented
        return Or(self, other)

    def __ror__(self, other: Union["Text", str]) -> "Or":
        if isinstance(other, str):
            other = Const(other)
        return Or(other, self)

    def find(self, widget_id: str) -> Optional["TextWidget"]:
        # no reimplementation, just change return type
        return cast(TextWidget | None, super().find(widget_id))


class Const(Text):
    def __init__(self, text: str, when: WhenCondition = None) -> None:
        super().__init__(when=when)
        self.text = text

    async def _render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        return self.text


class Multi(Text):
    def __init__(
        self,
        *texts: TextWidget,
        sep: str = "\n",
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.texts = texts
        self.sep = sep

    async def _render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        texts = [await t.render_text(data, manager) for t in self.texts]
        return self.sep.join(filter(None, texts))

    def __iadd__(self, other: TextWidget | str) -> Self:
        if isinstance(other, str):
            other = Const(other)
        self.texts += (other,)
        return self

    def __add__(self, other: TextWidget | str) -> "Multi":
        if isinstance(other, str):
            other = Const(other)
        if self.condition is true_condition and self.sep == "":
            # reduce nesting
            return Multi(*self.texts, other, sep="")
        return Multi(self, other, sep="")

    def __radd__(self, other: TextWidget | str) -> "Multi":
        if isinstance(other, str):
            other = Const(other)
        if self.condition is true_condition and self.sep == "":
            # reduce nesting
            return Multi(other, *self.texts, sep="")
        return Multi(other, self, sep="")

    def find(self, widget_id: str) -> TextWidget | None:
        for text in self.texts:
            if found := text.find(widget_id):
                return cast(TextWidget, found)
        return None


class Or(Text):
    def __init__(self, *texts: TextWidget) -> None:
        super().__init__()
        self.texts = texts

    async def _render_text(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> str:
        for text in self.texts:
            res = await text.render_text(data, manager)
            if res:
                return res
        return ""

    def __ior__(self, other: TextWidget | str) -> Self:
        if isinstance(other, str):
            other = Const(other)
        self.texts += (other,)
        return self

    def __or__(self, other: TextWidget | str) -> "Or":
        if isinstance(other, str):
            other = Const(other)
        # reduce nesting
        return Or(*self.texts, other)

    def __ror__(self, other: TextWidget | str) -> "Or":
        if isinstance(other, str):
            other = Const(other)
        # reduce nesting
        return Or(other, *self.texts)

    def find(self, widget_id: str) -> TextWidget | None:
        for text in self.texts:
            if found := text.find(widget_id):
                return cast(TextWidget, found)
        return None
