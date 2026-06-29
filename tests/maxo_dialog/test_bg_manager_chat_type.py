"""Regression tests for BgManager in 1:1 dialog chats.

Covers three related bugs:
- chat_type hardcoded to CHAT in BgManager (https://github.com/K1rL3s/maxo/pull/81)
- KeyError 'event_from_user' on DialogUpdateEvent (https://github.com/K1rL3s/maxo/issues/78)
- chat_id=None in UpdateContext for DialogUpdateEvent (https://github.com/K1rL3s/maxo/issues/79)
"""

import asyncio
from datetime import UTC, datetime

import pytest

from maxo import Ctx, Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.entities import DialogAction, DialogStartEvent
from maxo.dialogs.api.protocols import BgManagerFactory
from maxo.dialogs.manager.bg_manager import BgManager, BgManagerFactoryImpl
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.input import MessageInput
from maxo.dialogs.widgets.text import Format
from maxo.enums import ChatType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.middlewares.update_context import (
    EVENT_FROM_USER_KEY,
    UPDATE_CONTEXT_KEY,
    UpdateContextMiddleware,
)
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.updates import MessageCreated
from maxo.types import Recipient, User


class ChatSG(StatesGroup):
    active = State()


received_texts: list[str] = []


async def on_message(
    message: MessageCreated,
    widget: MessageInput,
    manager: DialogManager,
) -> None:
    text = message.message.body.text
    assert text is not None
    received_texts.append(text)


@pytest.fixture(autouse=True)
def _clear_received() -> None:
    received_texts.clear()


def _fake_user(user_id: int = 100) -> User:
    return User(
        user_id=user_id,
        is_bot=False,
        first_name="Test",
        last_activity_time=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Unit tests: chat_type propagation in BgManager (https://github.com/K1rL3s/maxo/pull/81)
# ---------------------------------------------------------------------------


class TestBgManagerChatTypePropagation:
    """BgManager and BgManagerFactoryImpl must accept and propagate chat_type."""

    def test_stores_chat_type_dialog(self) -> None:
        bg = BgManager(
            user=_fake_user(),
            chat_id=999,
            bot=FakeBot(),
            dp=Dispatcher(),
            intent_id=None,
            stack_id=None,
            chat_type=ChatType.DIALOG,
        )
        assert bg._event_context.chat_type == ChatType.DIALOG

    def test_defaults_to_chat(self) -> None:
        bg = BgManager(
            user=_fake_user(),
            chat_id=999,
            bot=FakeBot(),
            dp=Dispatcher(),
            intent_id=None,
            stack_id=None,
        )
        assert bg._event_context.chat_type == ChatType.CHAT

    def test_bg_inherits_chat_type(self) -> None:
        dp = Dispatcher()
        setup_dialogs(dp)
        bg = BgManager(
            user=_fake_user(),
            chat_id=999,
            bot=FakeBot(),
            dp=dp,
            intent_id=None,
            stack_id=None,
            chat_type=ChatType.DIALOG,
        )
        child = bg.bg(user_id=200, chat_id=888)
        assert isinstance(child, BgManager)
        assert child._event_context.chat_type == ChatType.DIALOG

    def test_factory_passes_chat_type(self) -> None:
        dp = Dispatcher()
        setup_dialogs(dp)
        factory = BgManagerFactoryImpl(dp)
        bg = factory.bg(FakeBot(), user_id=100, chat_id=999, chat_type=ChatType.DIALOG)
        assert isinstance(bg, BgManager)
        assert bg._event_context.chat_type == ChatType.DIALOG

    def test_factory_defaults_to_chat(self) -> None:
        dp = Dispatcher()
        setup_dialogs(dp)
        factory = BgManagerFactoryImpl(dp)
        bg = factory.bg(FakeBot(), user_id=100, chat_id=999)
        assert isinstance(bg, BgManager)
        assert bg._event_context.chat_type == ChatType.CHAT


# ---------------------------------------------------------------------------
# Unit test: UpdateContextMiddleware handles DialogUpdateEvent
# (https://github.com/K1rL3s/maxo/issues/78 + https://github.com/K1rL3s/maxo/issues/79)
# ---------------------------------------------------------------------------


class TestUpdateContextMiddlewareDialogEvent:
    """UpdateContextMiddleware must populate ctx for DialogUpdateEvent."""

    async def test_sets_event_from_user(self) -> None:
        """https://github.com/K1rL3s/maxo/issues/78: EVENT_FROM_USER_KEY must be set."""
        middleware = UpdateContextMiddleware()
        user = _fake_user(100)
        event = DialogStartEvent(
            action=DialogAction.START,
            data=None,
            new_state=ChatSG.active,
            mode=StartMode.RESET_STACK,
            show_mode=None,
            access_settings=None,
            user=user,
            recipient=Recipient(user_id=100, chat_id=999, chat_type=ChatType.DIALOG),
            bot=FakeBot(),
            intent_id=None,
            stack_id=None,
        )
        captured_ctx = Ctx({})

        async def next_handler(ctx: Ctx) -> None:
            captured_ctx.update(ctx)

        ctx = Ctx({})
        await middleware(MaxoUpdate(update=event), ctx, next_handler)

        assert EVENT_FROM_USER_KEY in captured_ctx
        assert captured_ctx[EVENT_FROM_USER_KEY].user_id == 100

    async def test_sets_update_context_with_chat_id(self) -> None:
        """https://github.com/K1rL3s/maxo/issues/79: chat_id must not be None."""
        middleware = UpdateContextMiddleware()
        user = _fake_user(100)
        event = DialogStartEvent(
            action=DialogAction.START,
            data=None,
            new_state=ChatSG.active,
            mode=StartMode.RESET_STACK,
            show_mode=None,
            access_settings=None,
            user=user,
            recipient=Recipient(user_id=100, chat_id=999, chat_type=ChatType.DIALOG),
            bot=FakeBot(),
            intent_id=None,
            stack_id=None,
        )
        captured_ctx = Ctx({})

        async def next_handler(ctx: Ctx) -> None:
            captured_ctx.update(ctx)

        ctx = Ctx({})
        await middleware(MaxoUpdate(update=event), ctx, next_handler)

        update_context = captured_ctx[UPDATE_CONTEXT_KEY]
        assert update_context.chat_id == 999
        assert update_context.user_id == 100
        assert update_context.type == ChatType.DIALOG


# ---------------------------------------------------------------------------
# Integration: bg.start(DIALOG) → send message → dialog handles it
# ---------------------------------------------------------------------------


def _make_dp(
    message_manager: MockMessageManager,
) -> tuple[Dispatcher, BgManagerFactory]:
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
                Format("chat active"),
                MessageInput(on_message),
                state=ChatSG.active,
            ),
        ),
    )
    bg_factory = setup_dialogs(
        dp,
        message_manager=message_manager,
        events_isolation=event_isolation,
    )
    return dp, bg_factory


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


async def test_bg_start_dialog_then_message_handled(
    message_manager: MockMessageManager,
) -> None:
    """Full pipeline: bg.start(chat_type=DIALOG) → send text → dialog handles it."""
    dp, bg_factory = _make_dp(message_manager)

    user_id = 100
    chat_id = 999  # Different from user_id - real Max 1:1 chat
    client = BotClient(dp, user_id=user_id, chat_id=chat_id, chat_type=ChatType.DIALOG)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    bg = bg_factory.bg(client.bot, user_id, chat_id, chat_type=ChatType.DIALOG)
    await bg.start(ChatSG.active, mode=StartMode.RESET_STACK)

    # bg.start() dispatches via call_soon + create_task - yield to event loop
    await asyncio.sleep(0.1)

    assert len(message_manager.sent_messages) >= 1
    assert message_manager.sent_messages[0].body.text == "chat active"

    message_manager.reset_history()
    await client.send("hello from user")

    assert received_texts == ["hello from user"]


async def test_bg_start_wrong_chat_type_message_unhandled(
    message_manager: MockMessageManager,
) -> None:
    """Without chat_type=DIALOG, dialog is unreachable (stack mismatch)."""
    dp, bg_factory = _make_dp(message_manager)

    user_id = 100
    chat_id = 999
    client = BotClient(dp, user_id=user_id, chat_id=chat_id, chat_type=ChatType.DIALOG)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    # Default ChatType.CHAT - wrong for 1:1 dialog
    bg = bg_factory.bg(client.bot, user_id, chat_id)
    await bg.start(ChatSG.active, mode=StartMode.RESET_STACK)

    await asyncio.sleep(0.1)

    message_manager.reset_history()
    await client.send("hello from user")

    # Message NOT handled - stack key mismatch ("<100>" vs "")
    assert received_texts == []
