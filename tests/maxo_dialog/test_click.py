from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock

from maxo import Dispatcher
from maxo.dialogs import Dialog, DialogManager, StartMode, Window, setup_dialogs
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.updates import MessageCallback, MessageCreated


class MainSG(StatesGroup):
    start = State()
    next = State()


async def on_click(
    event: MessageCallback,
    _button: Button,
    manager: DialogManager,
) -> None:
    await manager.middleware_data["usecase"]()
    await manager.next()


async def on_finish(
    event: MessageCallback,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.done()


async def second_getter(
    user_getter: Callable[[], Awaitable[str]],
    **_kwargs: Any,
) -> dict[str, Any]:
    return {"user": await user_getter()}


dialog = Dialog(
    Window(
        Format("stub"),
        Button(Const("Button"), id="hello", on_click=on_click),
        state=MainSG.start,
    ),
    Window(
        Format("Next {user}"),
        Button(Const("Finish"), id="hello", on_click=on_finish),
        state=MainSG.next,
        getter=second_getter,
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def test_click() -> None:
    usecase = AsyncMock()
    user_getter = AsyncMock(side_effect=["Username"])
    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        workflow_data={"usecase": usecase, "user_getter": user_getter},
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
    )
    dp.include(dialog)
    dp.message_created.handler(start, CommandStart())

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"
    assert first_message.body.reply_markup
    user_getter.assert_not_called()

    # redraw
    message_manager.reset_history()
    await client.send("whatever")

    first_message = message_manager.one_message()
    assert first_message.body.text == "stub"

    # click next
    message_manager.reset_history()
    callback_id = await client.click(first_message, InlineButtonTextLocator("Button"))

    message_manager.assert_answered(callback_id)
    usecase.assert_awaited()
    second_message = message_manager.one_message()
    assert second_message.body.text == "Next Username"
    assert second_message.body.reply_markup
    user_getter.assert_awaited_once()
