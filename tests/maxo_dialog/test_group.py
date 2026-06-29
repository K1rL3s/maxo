import asyncio
from typing import Any

import pytest

from maxo import Dispatcher
from maxo.dialogs import (
    BaseDialogManager,
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.entities import GROUP_STACK_ID, AccessSettings
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.enums import ChatType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import Command, CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    Button(Const("Button"), id="btn"),
    state=MainSG.start,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def start_shared(event: Any, dialog_manager: BaseDialogManager) -> None:
    dialog_manager = dialog_manager.bg(stack_id=GROUP_STACK_ID)
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def add_shared(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(
        MainSG.start,
        access_settings=AccessSettings(
            user_ids=[1, 2],
        ),
    )


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
    return BotClient(dp, chat_id=-1, user_id=1, chat_type=ChatType.CHAT)


@pytest.fixture
def second_client(dp: Dispatcher) -> BotClient:
    return BotClient(dp, chat_id=-1, user_id=2, chat_type=ChatType.CHAT)


async def test_second_user(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start, CommandStart())
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await second_client.send("test")
    assert not message_manager.sent_messages
    await second_client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_change_settings(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start, CommandStart())
    dp.message_created.handler(add_shared, Command("add"))

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    message_manager.reset_history()

    await client.send("/add")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    window_message = message_manager.one_message()
    message_manager.reset_history()
    assert window_message.body.text == "stub"

    await client.send("/start")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_change_settings_bg(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start, CommandStart())
    dp.message_created.handler(add_shared, Command("add"))

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    message_manager.reset_history()

    await client.send("/add")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    window_message = message_manager.one_message()
    message_manager.reset_history()
    assert window_message.body.text == "stub"

    await client.send("/start")
    window_message = message_manager.one_message()
    message_manager.reset_history()

    await second_client.click(
        window_message,
        InlineButtonTextLocator("Button"),
    )
    assert not message_manager.sent_messages


async def test_same_user(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start, CommandStart())

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await client.send("test")
    assert not message_manager.sent_messages  # no resend
    await client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_shared_stack(
    dp: Dispatcher,
    client: BotClient,
    second_client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.message_created.handler(start_shared, CommandStart())

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    await asyncio.sleep(0.1)  # synchronization workaround, fixme

    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    message_manager.reset_history()
    await second_client.send("test")
    assert not message_manager.sent_messages
    await second_client.click(
        first_message,
        InlineButtonTextLocator("Button"),
    )
    second_message = message_manager.one_message()
    assert second_message.body.text == "stub"
