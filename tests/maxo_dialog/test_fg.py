import asyncio
from collections.abc import Awaitable, Callable
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
from maxo.dialogs.api.entities import AccessSettings
from maxo.dialogs.api.exceptions import StackAccessDeniedError
from maxo.dialogs.api.protocols import BaseDialogManager
from maxo.dialogs.manager.bg_manager import BgManagerFactoryImpl
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.enums import ChatType
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import ErrorEvent

from .conftest import wait_for_messages


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
    await wait_for_messages(message_manager)
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


SHARED_STACK_ID = "shared"

BG_ACTIONS: dict[str, Callable[[BaseDialogManager], Awaitable[None]]] = {
    "start": lambda manager: manager.start(MainSG.start),
    "update": lambda manager: manager.update({"key": "value"}),
    "switch_to": lambda manager: manager.switch_to(MainSG.start),
    "done": lambda manager: manager.done(),
}


async def start_stack_for_first_user(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> BgManagerFactoryImpl:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    bg_factory = BgManagerFactoryImpl(dp)
    owner = bg_factory.bg(client.bot, user_id=1, chat_id=-1, stack_id=SHARED_STACK_ID)
    await owner.start(MainSG.start, access_settings=AccessSettings(user_ids=[1]))
    await wait_for_messages(message_manager)
    message_manager.reset_history()
    return bg_factory


@pytest.mark.parametrize("action", BG_ACTIONS)
async def test_bg_action_skipped_for_forbidden_stack(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
    action: str,
) -> None:
    errors: list[Exception] = []

    async def on_error(event: ErrorEvent[Any, Any]) -> None:
        errors.append(event.error)

    dp.exception.handler(on_error)
    bg_factory = await start_stack_for_first_user(dp, client, message_manager)

    stranger = bg_factory.bg(
        client.bot,
        user_id=2,
        chat_id=-1,
        stack_id=SHARED_STACK_ID,
    )
    await BG_ACTIONS[action](stranger)
    owner = bg_factory.bg(client.bot, user_id=1, chat_id=-1, stack_id=SHARED_STACK_ID)
    await owner.update()
    await wait_for_messages(message_manager)

    assert errors == []
    assert message_manager.one_message().body.text == "stub"


async def test_fg_raises_for_forbidden_stack(
    dp: Dispatcher,
    client: BotClient,
    message_manager: MockMessageManager,
) -> None:
    bg_factory = await start_stack_for_first_user(dp, client, message_manager)

    stranger = bg_factory.bg(
        client.bot,
        user_id=2,
        chat_id=-1,
        stack_id=SHARED_STACK_ID,
    )
    with pytest.raises(StackAccessDeniedError):
        async with asyncio.timeout(1), stranger.fg():
            pass
