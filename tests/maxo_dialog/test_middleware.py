from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from maxo import Dispatcher
from maxo.bot.bot import Bot
from maxo.dialogs import Dialog, DialogManager, StartMode, Window, setup_dialogs
from maxo.dialogs.api.entities import DialogUpdateEvent
from maxo.dialogs.manager.manager_middleware import BgFactoryMiddleware
from maxo.dialogs.test_tools import MockMessageManager
from maxo.dialogs.test_tools.bot_client import BotClient, FakeBot
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.text import Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.routing.ctx import Ctx
from maxo.routing.filters.command import CommandStart
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import BaseUpdate, MessageCreated

from .conftest import wait_for_messages


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


async def start_via_bg(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.bg().start(MainSG.start, mode=StartMode.RESET_STACK)


async def test_bg_factory_middleware_runs_once_per_dialog_event(
    message_manager: MockMessageManager,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dialog_events: list[DialogUpdateEvent] = []
    original_call: Callable[..., Awaitable[Any]] = BgFactoryMiddleware.__call__

    async def counting_call(
        self: BgFactoryMiddleware,
        update: BaseUpdate,
        ctx: Ctx,
        next: NextMiddleware[Any],
    ) -> Any:
        if isinstance(update, DialogUpdateEvent):
            dialog_events.append(update)
        return await original_call(self, update, ctx, next)

    monkeypatch.setattr(BgFactoryMiddleware, "__call__", counting_call)

    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp.message_created.handler(start_via_bg, CommandStart())
    dp.include(Dialog(Window(Format("stub"), state=MainSG.start)))
    setup_dialogs(dp, message_manager=message_manager)
    client = BotClient(dp)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)
    await client.send("/start")
    await wait_for_messages(message_manager)

    assert len(dialog_events) == 1
