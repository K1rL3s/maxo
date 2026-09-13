"""Тест каскадных переходов между вложенными диалогами.

Проверяет, что цепочка Main->Secondary->Third корректно запускается через
on_start колбэки, а Cancel во внутреннем диалоге каскадно возвращает
управление к корневому диалогу.
"""

import itertools
from typing import Any

import pytest

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.entities import stack
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Cancel
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import MessageCreated


class MainSG(StatesGroup):
    start = State()


class SecondarySG(StatesGroup):
    start = State()


class ThirdSG(StatesGroup):
    start = State()


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def on_start_main(data: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(SecondarySG.start)


async def on_start_sub(_: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(ThirdSG.start)


async def on_process_result_sub(_: Any, __: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.done()


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp)


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    dp = Dispatcher(storage=JsonMemoryStorage())
    dp.message_created.handler(start, CommandStart())

    dp.include(
        Dialog(
            Window(
                Const("First"),
                state=MainSG.start,
            ),
            on_start=on_start_main,
        ),
    )
    dp.include(
        Dialog(
            Window(
                Format("Subdialog"),
                Cancel(),
                state=SecondarySG.start,
            ),
            on_process_result=on_process_result_sub,
            on_start=on_start_sub,
        ),
    )
    dp.include(
        Dialog(
            Window(
                Format("Third"),
                Cancel(),
                state=ThirdSG.start,
            ),
        ),
    )
    setup_dialogs(dp, message_manager=message_manager)
    return dp


async def test_start(
    dp: Dispatcher,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "Third"
    assert first_message.body.reply_markup

    message_manager.reset_history()
    await client.click(first_message, InlineButtonTextLocator("Cancel"))
    second_message = message_manager.one_message()
    assert second_message.body.text == "First"
    assert second_message.body.reply_markup is None


@pytest.fixture(autouse=True)
def sequential_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(stack, "new_int_id", itertools.count(1).__next__)
