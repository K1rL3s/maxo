import operator
from typing import Any

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Select
from maxo.dialogs.widgets.text import Format


async def test_render_select(mock_manager: DialogManager) -> None:
    select: Select[Any] = Select(
        Format("{item[1]} ({pos}/3)"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=[("1", "Apple"), ("2", "Banana"), ("3", "Orange")],
    )

    keyboard = await select.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard[0]) == 3

    assert keyboard[0][0].text == "Apple (1/3)"
    assert keyboard[0][1].text == "Banana (2/3)"
    assert keyboard[0][2].text == "Orange (3/3)"
