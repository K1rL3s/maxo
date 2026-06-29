# tests for https://github.com/Tishka17/aiogram_dialog/issues/493

import pytest

from maxo import Dispatcher
from maxo.dialogs import Dialog, Window, setup_dialogs
from maxo.dialogs.widgets.text import Const
from maxo.fsm.state import State, StatesGroup
from maxo.routing.signals import AfterStartup


class First(StatesGroup):
    state = State()


class Second(StatesGroup):
    state = State()


async def test_one_state_group_per_dialog() -> None:
    first_dialog = Dialog(Window(Const("foo"), state=First.state))
    second_dialog = Dialog(Window(Const("bar"), state=First.state))
    dp = Dispatcher()
    dp.include(first_dialog, second_dialog)

    setup_dialogs(dp)
    with pytest.raises(
        ValueError,
        match=r"StatesGroup '.+' is used in multiple dialogs: '.+' and '.+'",
    ):
        await dp.feed_signal(AfterStartup())


def test_one_state_per_window() -> None:
    first_window = Window(Const("foo"), state=First.state)
    seconds_window = Window(Const("bar"), state=First.state)

    with pytest.raises(ValueError, match="Multiple windows with state"):
        Dialog(first_window, seconds_window)


def test_one_state_group_in_one_dialog() -> None:
    first_window = Window(Const("foo"), state=First.state)
    seconds_window = Window(Const("bar"), state=Second.state)

    with pytest.raises(
        ValueError,
        match="All windows must be attached to same StatesGroup",
    ):
        Dialog(first_window, seconds_window)
