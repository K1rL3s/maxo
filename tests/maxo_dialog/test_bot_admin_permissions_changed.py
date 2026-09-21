"""Диалоги из bot_admin_permissions_changed: в апдейте только user_id, без User."""

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
from maxo.dialogs.api.exceptions import UnknownIntent
from maxo.dialogs.context.storage import StorageProxy
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.enums import ChatType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import ExceptionTypeFilter
from maxo.routing.signals import AfterStartup, BeforeStartup, MaxoUpdate
from maxo.types import BotAdminPermissionsChanged
from tests.constants import NOW

from .conftest import wait_for_messages


class SettingsSG(StatesGroup):
    main = State()


async def get_counter(dialog_manager: DialogManager, **_: Any) -> dict[str, Any]:
    return {"counter": dialog_manager.dialog_data.get("counter", 0)}


async def increment(event: Any, button: Button, manager: DialogManager) -> None:
    manager.dialog_data["counter"] = manager.dialog_data.get("counter", 0) + 1


window = Window(
    Format("counter={counter}"),
    Button(Const("Добавить"), id="increment", on_click=increment),
    state=SettingsSG.main,
    getter=get_counter,
)


async def start(event: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(SettingsSG.main, mode=StartMode.RESET_STACK)


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
    return BotClient(dp, chat_id=-50, chat_type=ChatType.CHAT)


async def startup(client: BotClient) -> None:
    await client.dp.feed_signal(BeforeStartup(), client.bot)
    await client.dp.feed_signal(AfterStartup(), client.bot)


async def feed_admin_update(client: BotClient) -> None:
    update = BotAdminPermissionsChanged(
        chat_id=client.chat.chat_id,
        user_id=client.user.user_id,
        bot_id=client.bot.state.info.user_id,
        is_channel=False,
        is_admin=True,
        timestamp=NOW,
    )
    # Незакрытый лок стека подвесил бы прогон, поэтому с таймаутом
    await asyncio.wait_for(
        client.dp.feed_update(MaxoUpdate(update=update.as_(client.bot)), client.bot),
        timeout=5,
    )


async def test_dialog_started_from_update_keeps_state(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    dp.bot_admin_permissions_changed.handler(start)
    await startup(client)

    await feed_admin_update(client)
    message = message_manager.one_message()
    message_manager.reset_history()
    await asyncio.wait_for(
        client.click(message, InlineButtonTextLocator("Добавить")),
        timeout=5,
    )

    assert message_manager.one_message().body.text == "counter=1"


async def test_bg_manager_targets_current_stack(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    managers: list[BaseDialogManager] = []

    async def start_and_keep_bg(event: Any, dialog_manager: DialogManager) -> None:
        await start(event, dialog_manager)
        managers.append(dialog_manager.bg())

    dp.bot_admin_permissions_changed.handler(start_and_keep_bg)
    await startup(client)

    await feed_admin_update(client)
    await managers[0].update({"counter": 7})
    await wait_for_messages(message_manager, count=2)

    assert message_manager.last_message().body.text == "counter=7"


async def test_unknown_intent_handler_gets_dialog_manager(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    started: list[tuple[StorageProxy, str]] = []

    async def start_and_remember(event: Any, dialog_manager: DialogManager) -> None:
        await start(event, dialog_manager)
        started.append((dialog_manager.storage(), dialog_manager.current_context().id))

    dp.bot_admin_permissions_changed.handler(start_and_remember)
    dp.exception.handler(start, ExceptionTypeFilter(UnknownIntent))
    await startup(client)

    await feed_admin_update(client)
    storage, intent_id = started.pop()
    await storage.remove_context(intent_id)
    message_manager.reset_history()
    await feed_admin_update(client)

    assert message_manager.one_message().body.text == "counter=0"
