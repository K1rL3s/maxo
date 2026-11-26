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
from maxo.enums import ChatAdminPermission, ChatType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.omit import is_omitted
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup, MaxoUpdate
from maxo.types import BotAddedToChat, BotAdminPermissionsChanged, UpdateList


class MainSG(StatesGroup):
    start = State()


window = Window(
    Format("stub"),
    state=MainSG.start,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


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


async def test_bot_admin_permissions_changed(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.bot_admin_permissions_changed.handler(start)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.bot_admin_permissions_changed()
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"


async def test_bot_admin_permissions_changed_flags(
    dp: Dispatcher,
    client: BotClient,
) -> None:
    events: list[BotAdminPermissionsChanged] = []

    async def collect(
        event: BotAdminPermissionsChanged,
        dialog_manager: DialogManager,
    ) -> None:
        events.append(event)

    dp.bot_admin_permissions_changed.handler(collect)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    channel = BotClient(dp, chat_id=-10, chat_type=ChatType.CHANNEL, bot=client.bot)
    chat = BotClient(dp, chat_id=-20, chat_type=ChatType.CHAT, bot=client.bot)
    await channel.bot_admin_permissions_changed(
        permissions=[ChatAdminPermission.WRITE],
        is_admin=False,
    )
    await chat.bot_admin_permissions_changed()

    assert [event.is_channel for event in events] == [True, False]
    assert events[0].permissions == [ChatAdminPermission.WRITE]
    assert events[0].is_admin is False
    assert events[1].is_admin is True
    assert events[1].chat_id == -20


async def test_bot_added_without_user(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.bot_added_to_chat.handler(start)
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    updates = client.bot.retort.load(
        {
            "updates": [
                {
                    "update_type": "bot_added",
                    "timestamp": 1234567890,
                    "chat_id": client.chat.chat_id,
                    "is_channel": False,
                },
            ],
        },
        UpdateList,
    )
    update = updates.updates[0]
    assert isinstance(update, BotAddedToChat)
    assert is_omitted(update.user)
    await dp.feed_update(MaxoUpdate(update=update), client.bot)

    assert message_manager.one_message().body.text == "stub"
