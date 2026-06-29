from typing import Any

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities.link_preview import LinkPreviewOptions
from maxo.dialogs.api.internal import LinkPreviewWidget, TextWidget
from maxo.dialogs.widgets.common import BaseWidget, WhenCondition, Whenable
from maxo.omit import Omittable


class LinkPreviewBase(Whenable, BaseWidget, LinkPreviewWidget):
    def __init__(self, when: WhenCondition = None) -> None:
        super().__init__(when=when)

    async def render_link_preview(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> LinkPreviewOptions | None:
        if not self.is_(data, manager):
            return None
        return await self._render_link_preview(data, manager)

    async def _render_link_preview(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> LinkPreviewOptions | None:
        return None


class LinkPreview(LinkPreviewBase):
    def __init__(
        self,
        url: TextWidget | None = None,
        is_disabled: Omittable[bool] = False,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.url = url
        self.is_disabled = is_disabled

    async def render_link_preview(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> LinkPreviewOptions | None:
        if not self.is_(data, manager):
            return None
        return await self._render_link_preview(data, manager)

    async def _render_link_preview(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> LinkPreviewOptions | None:
        return LinkPreviewOptions(
            url=(await self.url.render_text(data, manager) if self.url else None),
            is_disabled=self.is_disabled,
        )
