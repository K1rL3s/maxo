from asyncio import Future
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from maxo.dialogs.api.entities import (
    AccessSettings,
    Context,
    DialogAction,
    DialogStartEvent,
    DialogSwitchEvent,
    DialogUpdateEvent,
    ShowMode,
    StartMode,
)
from maxo.dialogs.api.entities.update_event import DialogFgEvent
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.manager.update_handler import handle_aiogd_update
from maxo.fsm.state import State, StatesGroup


class TestStates(StatesGroup):
    first = State()
    second = State()


@pytest.fixture
def mock_dialog_manager() -> MagicMock:
    manager = MagicMock(spec=DialogManager)
    manager.start = AsyncMock()
    manager.switch_to = AsyncMock()
    manager.show = AsyncMock()
    manager.done = AsyncMock()
    manager.has_context = Mock(return_value=True)

    context = Context(
        dialog_data={},
        start_data={},
        widget_data={},
        state=TestStates.first,
        _stack_id="_stack_id",
        _intent_id="_intent_id",
    )
    manager.current_context = Mock(return_value=context)

    return manager


async def test_handle_dialog_start_event(mock_dialog_manager: MagicMock) -> None:
    event = DialogStartEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.START,
        data={"key": "value"},
        intent_id=None,
        stack_id=None,
        show_mode=ShowMode.EDIT,
        bot=MagicMock(),
        new_state=TestStates.first,
        mode=StartMode.RESET_STACK,
        access_settings=AccessSettings(user_ids=[1, 2, 3]),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    mock_dialog_manager.start.assert_called_once_with(
        state=TestStates.first,
        data={"key": "value"},
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT,
        access_settings=event.access_settings,
    )
    assert mock_dialog_manager.show_mode == ShowMode.EDIT


async def test_handle_dialog_switch_event(mock_dialog_manager: MagicMock) -> None:
    event = DialogSwitchEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.SWITCH,
        data=None,
        intent_id=None,
        stack_id=None,
        show_mode=ShowMode.AUTO,
        bot=MagicMock(),
        new_state=TestStates.second,
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    mock_dialog_manager.switch_to.assert_called_once_with(state=TestStates.second)
    mock_dialog_manager.show.assert_called_once()
    assert mock_dialog_manager.show_mode == ShowMode.AUTO


async def test_handle_dialog_fg_event(mock_dialog_manager: MagicMock) -> None:
    entered: Future[DialogManager] = Future()
    exited: Future[None] = Future()

    event = DialogFgEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.FG,
        data=None,
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
        entered=entered,
        exited=exited,
    )

    # Завершаем exited сразу, чтобы не повис тест
    exited.set_result(None)

    await handle_aiogd_update(event, mock_dialog_manager)

    assert entered.done()
    assert entered.result() == mock_dialog_manager


async def test_handle_dialog_update_event_with_context(
    mock_dialog_manager: MagicMock,
) -> None:
    event = DialogUpdateEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.UPDATE,
        data={"new_key": "new_value", "another_key": 42},
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    context = mock_dialog_manager.current_context()
    assert context.dialog_data["new_key"] == "new_value"
    assert context.dialog_data["another_key"] == 42
    mock_dialog_manager.show.assert_called_once()


async def test_handle_dialog_update_event_without_data(
    mock_dialog_manager: MagicMock,
) -> None:
    event = DialogUpdateEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.UPDATE,
        data=None,
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    mock_dialog_manager.show.assert_called_once()


async def test_handle_dialog_update_event_without_context(
    mock_dialog_manager: MagicMock,
) -> None:
    mock_dialog_manager.has_context.return_value = False

    event = DialogUpdateEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.UPDATE,
        data={"key": "value"},
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    # show не должен вызываться, когда нет контекста
    mock_dialog_manager.show.assert_not_called()


async def test_handle_dialog_done_event(mock_dialog_manager: MagicMock) -> None:
    event = DialogUpdateEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.DONE,
        data={"result": "success"},
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    mock_dialog_manager.done.assert_called_once_with(result={"result": "success"})


async def test_handle_dialog_start_event_with_none_show_mode(
    mock_dialog_manager: MagicMock,
) -> None:
    event = DialogStartEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.START,
        data={},
        intent_id=None,
        stack_id=None,
        show_mode=None,
        bot=MagicMock(),
        new_state=TestStates.first,
        mode=StartMode.NORMAL,
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    assert mock_dialog_manager.show_mode == ShowMode.AUTO


async def test_handle_dialog_fg_event_skips_cancelled_fg(
    mock_dialog_manager: MagicMock,
) -> None:
    entered: Future[DialogManager] = Future()
    entered.cancel()
    event = DialogFgEvent(
        user=MagicMock(),
        recipient=MagicMock(),
        action=DialogAction.FG,
        data=None,
        intent_id=None,
        stack_id=None,
        bot=MagicMock(),
        entered=entered,
        exited=Future(),
    )

    await handle_aiogd_update(event, mock_dialog_manager)

    assert entered.cancelled()
