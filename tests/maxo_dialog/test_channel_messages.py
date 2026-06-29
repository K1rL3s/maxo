"""Тесты обработки сообщений из каналов (без sender.user) - закрывает issue #111."""

from datetime import UTC, datetime
from typing import Any

import pytest

from maxo import Ctx, Dispatcher, Router
from maxo.dialogs import setup_dialogs
from maxo.dialogs.api.entities import AccessSettings, EventContext, Stack
from maxo.dialogs.api.entities.events import EVENT_CONTEXT_KEY
from maxo.dialogs.context.access_validator import DefaultAccessValidator
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.enums import ChatType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.routing.middlewares.update_context import (
    EVENT_FROM_USER_KEY,
    UPDATE_CONTEXT_KEY,
)
from maxo.routing.updates import MessageCreated
from maxo.types import Message, MessageBody, Recipient
from maxo.types.update_context import UpdateContext


@pytest.fixture
def captured_ctx() -> dict[str, Any]:
    return {}


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def dp(message_manager: MockMessageManager, captured_ctx: dict[str, Any]) -> Dispatcher:
    router = Router()

    @router.message_created()
    async def handler(event: Any, ctx: Ctx) -> None:
        captured_ctx["event_context"] = ctx[EVENT_CONTEXT_KEY]

    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp.include_router(router)
    setup_dialogs(dp, message_manager=message_manager)
    return dp


@pytest.fixture
def channel_client(dp: Dispatcher) -> BotClient:
    return BotClient(dp, user_id=1, chat_id=-100, chat_type=ChatType.CHANNEL)


@pytest.fixture
def event_message_created() -> MessageCreated:
    return MessageCreated(
        message=Message(
            recipient=Recipient(chat_type=ChatType.CHANNEL, chat_id=-100),
            timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
            body=MessageBody(mid="42", seq=42, text="channel post"),
        ),
        timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
    )


async def test_storage_proxy_channel_message_created(
    channel_client: BotClient,
    captured_ctx: dict[str, Any],
) -> None:
    """MessageCreated без sender.user не должен падать в storage_proxy."""
    await channel_client.send_channel_post("Привет канал")

    ev_ctx: EventContext = captured_ctx["event_context"]
    assert ev_ctx.user is None
    assert ev_ctx.user_id is None
    assert ev_ctx.chat_id == -100
    assert ev_ctx.chat_type == ChatType.CHANNEL


async def test_storage_proxy_channel_message_edited(
    channel_client: BotClient,
) -> None:
    """MessageEdited без sender тоже не падает (smoke - feed_update не кидает AttributeError)."""
    await channel_client.send_channel_message_edited("Edited", mid="42")


async def test_storage_proxy_channel_message_removed(
    channel_client: BotClient,
    captured_ctx: dict[str, Any],
) -> None:
    """MessageRemoved без user тоже не падает."""
    await channel_client.send_channel_message_removed(mid="42")


async def test_event_context_user_none_visible_in_handler(
    channel_client: BotClient,
    captured_ctx: dict[str, Any],
) -> None:
    """Хендлер видит EventContext с user=None при channel-посте."""
    await channel_client.send_channel_post("end-to-end")

    ev_ctx: EventContext = captured_ctx["event_context"]
    assert ev_ctx.bot is not None
    assert ev_ctx.user is None
    assert ev_ctx.user_id is None
    assert ev_ctx.chat_id == -100


async def test_access_validator_allows_when_no_settings(
    event_message_created: MessageCreated,
) -> None:
    """Если access_settings отсутствуют - доступ разрешён даже без user."""
    validator = DefaultAccessValidator()
    stack = Stack(_id="default", access_settings=None)
    ctx = Ctx({EVENT_FROM_USER_KEY: None})

    allowed = await validator.is_allowed(
        stack=stack,
        context=None,
        event=event_message_created,
        ctx=ctx,
    )

    assert allowed is True


async def test_access_validator_allows_in_dialog_chat(
    event_message_created: MessageCreated,
) -> None:
    """В приватном чате (DIALOG) доступ разрешён даже при заданных user_ids."""
    validator = DefaultAccessValidator()
    stack = Stack(
        _id="default",
        access_settings=AccessSettings(user_ids=[999]),
    )
    ctx = Ctx(
        {
            UPDATE_CONTEXT_KEY: UpdateContext(type=ChatType.DIALOG),
            EVENT_FROM_USER_KEY: None,
        },
    )

    allowed = await validator.is_allowed(
        stack=stack,
        context=None,
        event=event_message_created,
        ctx=ctx,
    )

    assert allowed is True


async def test_access_validator_denies_when_user_required_but_missing(
    event_message_created: MessageCreated,
) -> None:
    """В канале без user и при заданных user_ids - доступ запрещён (не AttributeError)."""
    validator = DefaultAccessValidator()
    stack = Stack(
        _id="default",
        access_settings=AccessSettings(user_ids=[1, 2, 3]),
    )
    ctx = Ctx(
        {
            UPDATE_CONTEXT_KEY: UpdateContext(type=ChatType.CHANNEL),
            EVENT_FROM_USER_KEY: None,
        },
    )

    allowed = await validator.is_allowed(
        stack=stack,
        context=None,
        event=event_message_created,
        ctx=ctx,
    )

    assert allowed is False
