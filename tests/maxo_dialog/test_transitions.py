import pytest

from maxo import Ctx, Dispatcher
from maxo.bot.bot import Bot
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Back, Cancel, Next, Start
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.updates import MessageCreated
from maxo.types import Message


class MainSG(StatesGroup):
    start = State()
    next = State()


class SecondarySG(StatesGroup):
    start = State()


async def start(
    message: MessageCreated,
    ctx: Ctx,
    dialog_manager: DialogManager,
) -> None:
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
    dp.message_created.handler(start, CommandStart())
    dp.include(
        Dialog(
            Window(
                Const("First"),
                Next(),
                Start(Const("Start"), state=SecondarySG.start, id="start"),
                Cancel(),
                state=MainSG.start,
            ),
            Window(
                Const("Second"),
                Back(),
                state=MainSG.next,
            ),
        ),
    )
    dp.include(
        Dialog(
            Window(
                Format("Subdialog"),
                Cancel(),
                state=SecondarySG.start,
            ),
        ),
    )
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)
    return dp


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp)


@pytest.fixture
def bot() -> Bot:
    return FakeBot()


async def test_start(
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "First"
    assert first_message.body.keyboard


async def test_next_back(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # click next
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Next"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Second"

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Back"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.body.keyboard


async def test_finish_last(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.body.keyboard, "Keyboard closed"


async def test_reset_stack(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    first_message: Message | None = None
    for _ in range(200):
        message_manager.reset_history()
        await client.send("/start")
        first_message = message_manager.one_message()
        assert first_message.body.text == "First"

    message_manager.reset_history()

    assert first_message is not None
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.body.keyboard, "Keyboard closed"


async def test_subdialog(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # start subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Start"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Subdialog"

    # close subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.body.keyboard
