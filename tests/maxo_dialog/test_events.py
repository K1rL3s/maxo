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
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.text import Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    state=MainSG.start,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
    )
    dp.include(Dialog(window))
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)
    return dp


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp)


async def test_click(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start, CommandStart())
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_request_join(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.user_added_to_chat.handler(start)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.user_added_to_chat()
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_my_chat_member_update(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.bot_added_to_chat.handler(start)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.bot_added_to_chat()
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
