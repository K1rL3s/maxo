import operator
from typing import Any, cast
from unittest.mock import AsyncMock

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.widgets.kbd import Toggle
from maxo.dialogs.widgets.text import Format


async def test_render_toggle(mock_manager: DialogManager) -> None:
    toggle: Toggle[Any] = Toggle(
        Format("{item[1]}"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=[("1", "Apple"), ("2", "Banana"), ("3", "Orange")],
    )

    keyboard = await toggle.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert keyboard[0][0].text == "Apple"

    await toggle.set_checked(cast(ChatEvent, AsyncMock()), "2", mock_manager)

    keyboard = await toggle.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert keyboard[0][0].text == "Banana"
