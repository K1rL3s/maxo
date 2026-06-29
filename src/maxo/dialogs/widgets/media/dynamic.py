"""
Dynamic media.

Originally developed in maxo-dialog-extras project
https://github.com/SamWarden/maxo_dialog_extras
"""

from collections.abc import Callable
from operator import itemgetter
from typing import Any

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.media import Media

MediaSelector = Callable[[dict], list[MediaAttachment]]


class DynamicMedia(Media):
    def __init__(
        self,
        selector: str | MediaSelector,
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        if isinstance(selector, str):
            self.selector: MediaSelector = itemgetter(selector)
        else:
            self.selector = selector

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        media: list[MediaAttachment] = self.selector(data)
        return media
