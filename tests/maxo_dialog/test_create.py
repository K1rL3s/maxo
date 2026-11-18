from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import Dispatcher
from maxo.dialogs import Dialog, Window, setup_dialogs
from maxo.dialogs.api.entities import Context
from maxo.dialogs.api.exceptions import UnregisteredWindowError
from maxo.dialogs.api.protocols import CancelEventProcessing
from maxo.dialogs.widgets.text import Format
from maxo.enums import ChatType
from maxo.fsm.state import State, StatesGroup
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY, UpdateContext
from maxo.types import Callback, MessageCallback, User
from tests.constants import NOW


class MainSG(StatesGroup):
    start = State()


def test_register() -> None:
    dialog = Dialog(
        Window(
            Format("stub"),
            state=MainSG.start,
        ),
    )

    dp = Dispatcher()
    dp.include(dialog)
    setup_dialogs(dp)


def test_name_state_group() -> None:
    dialog = Dialog(
        Window(
            Format("stub"),
            state=MainSG.start,
        ),
    )
    assert dialog.name == "MainSG"


def test_name_explicit() -> None:
    dialog = Dialog(
        Window(
            Format("stub"),
            state=MainSG.start,
        ),
        name="FooDialog",
    )
    assert dialog.name == "FooDialog"


class OtherSG(StatesGroup):
    start = State()


def make_dialog() -> Dialog:
    return Dialog(Window(Format("stub"), state=MainSG.start))


def make_manager(state: State = MainSG.start) -> MagicMock:
    context = Context(
        _intent_id="i",
        _stack_id="s",
        state=state,
        start_data={},
        widget_data={},
        dialog_data={},
    )
    manager = MagicMock()
    manager.current_context = MagicMock(return_value=context)
    manager.has_context = MagicMock(return_value=True)
    manager.switch_to = AsyncMock()
    manager.show = AsyncMock()
    manager.answer_callback = AsyncMock()
    manager.load_data = AsyncMock(return_value={})
    manager.middleware_data = {
        UPDATE_CONTEXT_KEY: UpdateContext(chat_id=1, user_id=1, type=ChatType.DIALOG),
    }
    return manager


def test_dialog_without_windows() -> None:
    with pytest.raises(ValueError, match="at least one window"):
        Dialog()


def test_windows_from_different_groups() -> None:
    with pytest.raises(ValueError, match="same StatesGroup"):
        Dialog(
            Window(Format("a"), state=MainSG.start),
            Window(Format("b"), state=OtherSG.start),
        )


def test_duplicate_window_state() -> None:
    with pytest.raises(ValueError, match="Multiple windows"):
        Dialog(
            Window(Format("a"), state=MainSG.start),
            Window(Format("b"), state=MainSG.start),
        )


def test_include_is_forbidden() -> None:
    with pytest.raises(TypeError, match="cannot include routers"):
        make_dialog().include(Dispatcher())


async def test_current_window_for_unknown_state() -> None:
    dialog = make_dialog()

    with pytest.raises(UnregisteredWindowError, match="No window found"):
        await dialog._current_window(make_manager(OtherSG.start))


async def test_process_start_uses_first_state() -> None:
    dialog = make_dialog()
    manager = make_manager()

    await dialog.process_start(manager, start_data={})

    manager.switch_to.assert_awaited_once_with(MainSG.start)


async def test_process_start_calls_on_start() -> None:
    on_start = AsyncMock()
    dialog = Dialog(Window(Format("stub"), state=MainSG.start), on_start=on_start)

    await dialog.process_start(make_manager(), start_data={"a": 1})

    on_start.assert_awaited_once()


async def test_process_close_calls_on_close() -> None:
    on_close = AsyncMock()
    dialog = Dialog(Window(Format("stub"), state=MainSG.start), on_close=on_close)

    await dialog.process_close("result", make_manager())

    on_close.assert_awaited_once()


async def test_message_handler_swallows_cancel_event() -> None:
    dialog = make_dialog()
    manager = make_manager()
    dialog.windows[MainSG.start].process_message = AsyncMock(  # type: ignore[method-assign]
        side_effect=CancelEventProcessing,
    )

    await dialog._message_handler(MagicMock(), {}, manager)  # type: ignore[arg-type]

    manager.show.assert_awaited_once()


async def test_callback_handler_swallows_cancel_event() -> None:
    dialog = make_dialog()
    manager = make_manager()
    dialog.windows[MainSG.start].process_callback = AsyncMock(  # type: ignore[method-assign]
        side_effect=CancelEventProcessing,
    )
    callback = MessageCallback(
        timestamp=NOW,
        callback=Callback(
            callback_id="c",
            timestamp=NOW,
            payload="p",
            user=User(
                user_id=1,
                is_bot=False,
                first_name="U",
                last_activity_time=NOW,
            ),
        ),
    )

    await dialog._callback_handler(callback, {}, manager)  # type: ignore[arg-type]

    manager.answer_callback.assert_awaited_once()


def test_need_refresh_without_context() -> None:
    dialog = make_dialog()
    manager = make_manager()
    manager.has_context = MagicMock(return_value=False)

    assert dialog._need_refresh(True, manager.current_context(), manager) is False


def test_need_refresh_after_dialog_switch() -> None:
    dialog = make_dialog()
    manager = make_manager()
    other = Context(
        _intent_id="other-intent",
        _stack_id="s",
        state=OtherSG.start,
        start_data={},
        widget_data={},
        dialog_data={},
    )

    assert dialog._need_refresh(True, other, manager) is False


def test_need_refresh_in_group_chat_without_processing() -> None:
    dialog = make_dialog()
    manager = make_manager()
    manager.middleware_data[UPDATE_CONTEXT_KEY] = UpdateContext(
        chat_id=1,
        user_id=1,
        type=ChatType.CHAT,
    )

    assert dialog._need_refresh(False, manager.current_context(), manager) is False
