from unittest.mock import AsyncMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.media import MediaScroll, StaticMedia
from maxo.dialogs.widgets.text import Format


async def test_render_media_scroll(mock_manager: DialogManager) -> None:
    media = MediaScroll(
        items=["0.png", "1.png", "2.png"],
        media=StaticMedia(path=Format("/{item}")),
        id="m",
    )
    res = await media.render_media(data={}, manager=mock_manager)
    assert len(res) == 1
    assert res[0].path == "/0.png"

    await media.set_page(event=AsyncMock(), page=2, manager=mock_manager)
    res = await media.render_media(data={}, manager=mock_manager)
    assert len(res) == 1
    assert res[0].path == "/2.png"

    managed = media.managed(mock_manager)
    await managed.set_page(1)
    res = await media.render_media(data={}, manager=mock_manager)
    assert len(res) == 1
    assert res[0].path == "/1.png"
