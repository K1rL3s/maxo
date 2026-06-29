import pytest

from maxo import Dispatcher
from maxo.bot.bot import Bot
from maxo.dialogs import Dialog, DialogManager, StartMode, Window, setup_dialogs
from maxo.dialogs.test_tools import MockMessageManager
from maxo.dialogs.test_tools.bot_client import BotClient, FakeBot
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.text import Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.routing.ctx import Ctx
from maxo.routing.filters.command import CommandStart
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.routing.updates import MessageCreated


class MainSG(StatesGroup):
    start = State()


class MyMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> None:
        ctx["my_key"] = "my_value"
        await next(ctx)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp.message_created.handler(start, CommandStart())
    dp.include(
        Dialog(
            Window(
                Format("{middleware_data[my_key]}"),
                state=MainSG.start,
            ),
        ),
    )
    dp.message_created.middleware.outer(MyMiddleware())
    setup_dialogs(dp, message_manager=message_manager)
    return dp


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp)


@pytest.fixture
def bot() -> Bot:
    return FakeBot()


async def test_middleware(
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "my_value"
