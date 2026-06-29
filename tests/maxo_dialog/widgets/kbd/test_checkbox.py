from typing import cast
from unittest.mock import AsyncMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.widgets.kbd import Checkbox
from maxo.dialogs.widgets.text import Const


async def test_check_checkbox(mock_manager: DialogManager) -> None:
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        default=True,
    )

    assert checkbox.is_checked(mock_manager)

    await checkbox.set_checked(cast(ChatEvent, Mock()), False, mock_manager)

    assert not checkbox.is_checked(mock_manager)


async def test_on_state_changed_checkbox(mock_manager: DialogManager) -> None:
    on_state_changed = AsyncMock()
    checkbox = Checkbox(
        Const("✓  Checked"),
        Const("Unchecked"),
        id="check",
        on_state_changed=on_state_changed,
    )

    await checkbox.set_checked(cast(ChatEvent, Mock()), False, mock_manager)

    on_state_changed.assert_called_once()
