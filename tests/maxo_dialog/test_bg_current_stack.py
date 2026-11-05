from typing import Any

import pytest

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    ShowMode,
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
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import MessageCallback, MessageCreated

from .conftest import wait_for_messages


class BgSG(StatesGroup):
    start = State()


async def get_value(dialog_manager: DialogManager, **kwargs: Any) -> dict[str, Any]:
    return {"value": dialog_manager.dialog_data.get("value", 0)}


async def bump_in_bg(
    event: MessageCallback,
    button: Button,
    manager: DialogManager,
) -> None:
    manager.show_mode = ShowMode.NO_UPDATE
    await manager.bg().update({"value": 1})


async def start_new_stack(event: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(BgSG.start, mode=StartMode.NEW_STACK)


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
    )
    dp.include(
        Dialog(
            Window(
                Format("value={value}"),
                Button(Const("Bump"), id="bump", on_click=bump_in_bg),
                state=BgSG.start,
                getter=get_value,
            ),
        ),
    )
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)
    return dp


async def test_bg_without_stack_id_updates_current_stack(
    dp: Dispatcher,
    message_manager: MockMessageManager,
) -> None:
    client = BotClient(dp, chat_id=-1, user_id=1, chat_type=ChatType.CHAT)
    dp.message_created.handler(start_new_stack, CommandStart())
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    await wait_for_messages(message_manager)
    window_message = message_manager.one_message()
    assert window_message.body.text == "value=0"
    message_manager.reset_history()

    await client.click(window_message, InlineButtonTextLocator("Bump"))

    await wait_for_messages(message_manager)
    assert message_manager.one_message().body.text == "value=1"
