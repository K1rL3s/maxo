from typing import Any

from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.media import Media
from maxo.enums import AttachmentType


class Static(Media):
    def __init__(self, path: str, when: WhenCondition = None) -> None:
        super().__init__(when=when)
        self.path = path

    async def _render_media(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> list[MediaAttachment]:
        return [MediaAttachment(AttachmentType.IMAGE, path=self.path)]


async def test_or(mock_manager: DialogManager) -> None:
    text = Static("a") | Static("b")
    res = await text.render_media({}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="a")]


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = Static("A", when=F["a"]) | Static("B", when=F["b"]) | Static("C")
    res = await text.render_media({"a": True}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="A")]
    res = await text.render_media({"b": True}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="B")]
    res = await text.render_media({}, mock_manager)
    assert res == [MediaAttachment(AttachmentType.IMAGE, path="C")]
