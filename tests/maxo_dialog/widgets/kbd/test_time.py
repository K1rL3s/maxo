import datetime

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import TimeSelect


async def test_render_time_select(mock_manager: DialogManager) -> None:
    select = TimeSelect("x")

    keyboard_before = await select.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert len(keyboard_before) == 8

    await select.set_value(
        mock_manager.event,
        mock_manager,
        datetime.time(0, 10),
    )

    keyboard_after = await select.render_keyboard(
        data={},
        manager=mock_manager,
    )

    assert len(keyboard_after) == 8
    assert keyboard_after != keyboard_before
