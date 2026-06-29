import asyncio
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
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.enums import ChatType
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    Button(Const("Button"), id="btn"),
    state=MainSG.start,
)


async def start_for_second_user(
    event: Any,
    dialog_manager: DialogManager,
) -> None:
    async with dialog_manager.bg(user_id=2, chat_id=-1).fg() as manager:
        await manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def start_for_second_user_via_bg(
    event: Any,
    dialog_manager: DialogManager,
) -> None:
    manager = dialog_manager.bg(user_id=2, chat_id=-1)
    await manager.start(MainSG.start, mode=StartMode.RESET_STACK)


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    dp = Dispatcher(storage=JsonMemoryStorage())
    dp.include_router(Dialog(window))
    setup_dialogs(dp, message_manager=message_manager)
    return dp


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp, chat_id=-1, user_id=1, chat_type=ChatType.CHAT)


@pytest.fixture
def second_client(dp: Dispatcher) -> BotClient:
    return BotClient(dp, chat_id=-1, user_id=2, chat_type=ChatType.CHAT)


async def test_start_in_foreground_for_another_user(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message.register(start_for_second_user, CommandStart())

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    window_message = message_manager.one_message()
    assert window_message.body.text == "stub"
    message_manager.reset_history()

    await client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    second_message = message_manager.one_message()
    assert second_message.body.text == "stub"


async def test_start_in_foreground_for_another_user_via_bg(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message.register(start_for_second_user_via_bg, CommandStart())

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    await asyncio.sleep(0.1)
    window_message = message_manager.one_message()
    assert window_message.body.text == "stub"
    message_manager.reset_history()

    await client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    second_message = message_manager.one_message()
    assert second_message.body.text == "stub"
