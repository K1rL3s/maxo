import itertools
from typing import Any, Self

from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.api.internal import MediaWidget
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.utils import add_exception_note
from maxo.dialogs.widgets.common import (
    BaseWidget,
    WhenCondition,
    Whenable,
    true_condition,
)


class Media(Whenable, BaseWidget, MediaWidget):
    def __init__(self, when: WhenCondition = None) -> None:
        super().__init__(when=when)

    @add_exception_note
    async def render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        if not self.is_(data, manager):
            return []
        return await self._render_media(data, manager)

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        return []

    def __or__(self, other: "Media") -> "Or":
        # reduce nesting
        if isinstance(other, Or):
            return NotImplemented
        return Or(self, other)

    def __ror__(self, other: "Media") -> "Or":
        # reduce nesting
        return Or(other, self)

    def __add__(self, other: "Media") -> "MultiMedia":
        if isinstance(other, MultiMedia):
            return NotImplemented
        return MultiMedia(self, other)

    def __radd__(self, other: "Media") -> "MultiMedia":
        return MultiMedia(other, self)

    def find(self, widget_id: str) -> "Media | None":
        # no reimplementation, just change return type
        return super().find(widget_id)


class MultiMedia(Media):
    def __init__(
        self,
        *media: Media,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.media = media

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        media = [await m.render_media(data, manager) for m in self.media]
        return list(itertools.chain(*media))

    def __iadd__(self, other: Media) -> Self:
        self.media += (other,)
        return self

    def __add__(self, other: Media) -> "MultiMedia":
        if self.condition is true_condition:
            # reduce nesting
            return MultiMedia(*self.media, other)
        return MultiMedia(self, other)

    def __radd__(self, other: Media) -> "MultiMedia":
        if self.condition is true_condition:
            # reduce nesting
            return MultiMedia(other, *self.media)
        return MultiMedia(other, self)

    def find(self, widget_id: str) -> Media | None:
        for text in self.media:
            if found := text.find(widget_id):
                return found
        return None


class Or(Media):
    def __init__(self, *widgets: Media) -> None:
        super().__init__()
        self.widgets = widgets

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        for widget in self.widgets:
            res = await widget.render_media(data, manager)
            if res:
                return res
        return []

    def __ior__(self, other: Media) -> Self:
        self.widgets += (other,)
        return self

    def __or__(self, other: Media) -> "Or":
        # reduce nesting
        return Or(*self.widgets, other)

    def __ror__(self, other: Media) -> "Or":
        # reduce nesting
        return Or(other, *self.widgets)
