from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs.api.entities import (
    DEFAULT_STACK_ID,
    EVENT_CONTEXT_KEY,
    DialogAction,
    DialogUpdateEvent,
    Stack,
)
from maxo.dialogs.api.exceptions import (
    InvalidStackIdError,
    OutdatedIntent,
    UnknownIntent,
)
from maxo.dialogs.api.internal import (
    CALLBACK_DATA_KEY,
    CONTEXT_KEY,
    PAYLOAD_KEY,
    STACK_KEY,
    STORAGE_KEY,
)
from maxo.dialogs.context.access_validator import DefaultAccessValidator
from maxo.dialogs.context.intent_middleware import (
    FORBIDDEN_STACK_KEY,
    IntentErrorMiddleware,
    IntentMiddlewareFactory,
    event_context_from_aiogd,
    event_context_from_bot_started,
    event_context_from_callback,
    event_context_from_error,
    event_context_from_user_added_to_chat,
)
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.enums import ChatType
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.omit import Omitted
from maxo.routing.middlewares.fsm_context import FSM_STORAGE_KEY
from maxo.routing.middlewares.update_context import (
    EVENT_FROM_USER_KEY,
    UPDATE_CONTEXT_KEY,
)
from maxo.types import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    Callback,
    Message,
    MessageBody,
    MessageCallback,
    Recipient,
    UpdateContext,
    UserAddedToChat,
    UserRemovedFromChat,
)
from tests.constants import NOW

from .conftest import make_message_created, make_user


class SG(StatesGroup):
    first = State()


def make_ctx(bot: Any = None) -> dict[Any, Any]:
    return {
        "bot": bot or MagicMock(),
        FSM_STORAGE_KEY: JsonMemoryStorage(),
        UPDATE_CONTEXT_KEY: UpdateContext(chat_id=10, user_id=1, type=ChatType.DIALOG),
        EVENT_FROM_USER_KEY: make_user(),
    }


def make_callback(payload: str = "data") -> Callback:
    return Callback(
        callback_id="c",
        user=make_user(),
        timestamp=NOW,
        payload=payload,
    )


def make_message_callback(payload: str = "data") -> MessageCallback:
    return MessageCallback(
        timestamp=NOW,
        message=Message(
            timestamp=NOW,
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
            body=MessageBody(mid="m", seq=1),
        ),
        callback=make_callback(payload),
    )


def make_message_callback_without_message(payload: str = "data") -> MessageCallback:
    """Колбэк с удалённым исходным сообщением: `message` приходит как `null`."""
    return MessageCallback(
        timestamp=NOW,
        message=None,
        callback=make_callback(payload),
    )


def make_aiogd_event(
    intent_id: str | None = None,
    stack_id: str | None = DEFAULT_STACK_ID,
) -> DialogUpdateEvent:
    return DialogUpdateEvent(
        user=make_user(),
        recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
        bot=MagicMock(),
        action=DialogAction.UPDATE,
        data={},
        intent_id=intent_id,
        stack_id=stack_id,
    )


def make_bot_started() -> BotStarted:
    return BotStarted(timestamp=NOW, chat_id=10, user=make_user())


def make_bot_stopped() -> BotStopped:
    return BotStopped(timestamp=NOW, chat_id=10, user=make_user())


def make_user_added() -> UserAddedToChat:
    return UserAddedToChat(
        timestamp=NOW,
        chat_id=10,
        user=make_user(),
        is_channel=False,
    )


def make_user_removed() -> UserRemovedFromChat:
    return UserRemovedFromChat(
        timestamp=NOW,
        chat_id=10,
        user=make_user(),
        is_channel=False,
    )


def make_bot_added() -> BotAddedToChat:
    return BotAddedToChat(
        timestamp=NOW,
        chat_id=10,
        user=make_user(),
        is_channel=False,
    )


def make_bot_removed() -> BotRemovedFromChat:
    return BotRemovedFromChat(
        timestamp=NOW,
        chat_id=10,
        user=make_user(),
        is_channel=False,
    )


CHAT_EVENT_HANDLERS = [
    ("process_bot_started", make_bot_started),
    ("process_bot_stopped", make_bot_stopped),
    ("process_user_added_to_chat", make_user_added),
    ("process_user_removed_from_chat", make_user_removed),
    ("process_bot_added_to_chat", make_bot_added),
    ("process_bot_removed_from_chat", make_bot_removed),
]


def make_isolation() -> SimpleEventIsolation:
    # StorageProxy строит ключ лока с destiny
    return SimpleEventIsolation(DefaultKeyBuilder(with_destiny=True))


def make_factory() -> IntentMiddlewareFactory:
    registry = MagicMock()
    registry.states_groups.return_value = {"SG": SG}
    return IntentMiddlewareFactory(
        registry=registry,
        access_validator=DefaultAccessValidator(),
        events_isolation=make_isolation(),
    )


class TestEventContextBuilders:
    def test_from_bot_started(self) -> None:
        event = BotStarted(timestamp=NOW, chat_id=10, user=make_user())

        context = event_context_from_bot_started(event, make_ctx())  # type: ignore[arg-type]

        assert context.chat_type is ChatType.DIALOG
        assert context.chat_id == 10
        assert context.user_id == 1

    def test_from_user_added_to_chat_in_chat(self) -> None:
        event = UserAddedToChat(
            timestamp=NOW,
            chat_id=10,
            user=make_user(),
            is_channel=False,
        )

        context = event_context_from_user_added_to_chat(event, make_ctx())  # type: ignore[arg-type]

        assert context.chat_type is ChatType.CHAT

    def test_from_user_added_to_channel(self) -> None:
        event = UserAddedToChat(
            timestamp=NOW,
            chat_id=10,
            user=make_user(),
            is_channel=True,
        )

        context = event_context_from_user_added_to_chat(event, make_ctx())  # type: ignore[arg-type]

        assert context.chat_type is ChatType.CHANNEL

    def test_from_aiogd(self) -> None:
        context = event_context_from_aiogd(make_aiogd_event())

        assert context.chat_id == 10
        assert context.user_id == 1

    def test_from_callback(self) -> None:
        context = event_context_from_callback(make_message_callback(), make_ctx())  # type: ignore[arg-type]

        assert context.chat_id == 10
        assert context.chat_type is ChatType.DIALOG
        assert context.user_id == 1

    def test_from_callback_without_message(self) -> None:
        event = make_message_callback_without_message()

        context = event_context_from_callback(event, make_ctx())  # type: ignore[arg-type]

        assert context.chat_id is None
        assert context.chat_type is None
        assert context.user_id == 1
        assert context.user is event.callback.user


class TestEventContextFromError:
    @pytest.mark.parametrize(
        "make_event",
        [
            make_message_created,
            make_message_callback,
            make_message_callback_without_message,
            make_aiogd_event,
            make_bot_started,
            make_bot_stopped,
            make_user_added,
            make_user_removed,
            make_bot_added,
            make_bot_removed,
        ],
        ids=lambda f: f.__name__,
    )
    def test_supported_events(self, make_event: Any) -> None:
        error_event = MagicMock(event=make_event())

        assert event_context_from_error(error_event, make_ctx()) is not None  # type: ignore[arg-type]

    def test_unsupported_event(self) -> None:
        error_event = MagicMock(event=object())

        with pytest.raises(ValueError, match="Unsupported event"):
            event_context_from_error(error_event, make_ctx())  # type: ignore[arg-type]


class TestIntentMiddlewareFactory:
    def test_check_outdated_on_empty_stack(self) -> None:
        with pytest.raises(OutdatedIntent):
            make_factory()._check_outdated("intent", Stack())

    def test_check_outdated_on_other_intent(self) -> None:
        stack = Stack()
        stack.push(SG.first, {})

        with pytest.raises(OutdatedIntent):
            make_factory()._check_outdated("other", stack)

    def test_check_outdated_passes_for_last_intent(self) -> None:
        stack = Stack()
        stack.push(SG.first, {})

        make_factory()._check_outdated(stack.last_intent_id(), stack)

    async def test_load_stack_without_id(self) -> None:
        with pytest.raises(InvalidStackIdError):
            await make_factory()._load_stack(None, MagicMock())

    async def test_process_message_loads_default_context(self) -> None:
        ctx = make_ctx()
        next_ = AsyncMock(return_value="ok")

        result = await make_factory().process_message(
            make_message_created(),
            ctx,  # type: ignore[arg-type]
            next_,
        )

        assert result == "ok"
        assert ctx[EVENT_CONTEXT_KEY] is not None
        assert ctx[STORAGE_KEY] is not None
        assert ctx[STACK_KEY].id == DEFAULT_STACK_ID
        assert ctx[CONTEXT_KEY] is None

    async def test_process_callback_without_update_context(self) -> None:
        ctx: dict[Any, Any] = {}
        next_ = AsyncMock(return_value="skipped")

        result = await make_factory().process_callback(
            make_message_callback(),
            ctx,  # type: ignore[arg-type]
            next_,
        )

        assert result == "skipped"
        assert EVENT_CONTEXT_KEY not in ctx

    async def test_process_callback_stores_payload(self) -> None:
        ctx = make_ctx()
        next_ = AsyncMock(return_value="ok")

        await make_factory().process_callback(
            make_message_callback("plain"),
            ctx,  # type: ignore[arg-type]
            next_,
        )

        assert ctx[PAYLOAD_KEY] == "plain"
        assert ctx[CALLBACK_DATA_KEY] == "plain"

    async def test_process_callback_without_message(self) -> None:
        ctx = make_ctx()
        next_ = AsyncMock(return_value="ok")

        result = await make_factory().process_callback(
            make_message_callback_without_message("plain"),
            ctx,  # type: ignore[arg-type]
            next_,
        )

        assert result == "ok"
        next_.assert_awaited_once()
        assert ctx[EVENT_CONTEXT_KEY].chat_id is None

    async def test_process_aiogd_update_by_stack(self) -> None:
        ctx = make_ctx()
        next_ = AsyncMock(return_value="ok")

        await make_factory().process_aiogd_update(
            make_aiogd_event(),
            ctx,  # type: ignore[arg-type]
            next_,
        )

        assert ctx[STACK_KEY].id == DEFAULT_STACK_ID

    async def test_process_aiogd_update_by_unknown_intent(self) -> None:
        ctx = make_ctx()

        with pytest.raises(UnknownIntent):
            await make_factory().process_aiogd_update(
                make_aiogd_event(intent_id="missing"),
                ctx,  # type: ignore[arg-type]
                AsyncMock(),
            )

    @pytest.mark.parametrize(("method", "make_event"), CHAT_EVENT_HANDLERS)
    async def test_process_chat_events(self, method: str, make_event: Any) -> None:
        ctx = make_ctx()
        next_ = AsyncMock(return_value="ok")

        result = await getattr(make_factory(), method)(make_event(), ctx, next_)

        assert result == "ok"
        assert ctx[EVENT_CONTEXT_KEY] is not None
        assert ctx[STORAGE_KEY] is not None
        assert ctx[CONTEXT_KEY] is None

    @pytest.mark.parametrize(("method", "make_event"), CHAT_EVENT_HANDLERS)
    async def test_process_chat_events_without_update_context(
        self,
        method: str,
        make_event: Any,
    ) -> None:
        ctx: dict[Any, Any] = {}
        next_ = AsyncMock(return_value="skipped")

        result = await getattr(make_factory(), method)(make_event(), ctx, next_)

        assert result == "skipped"
        assert EVENT_CONTEXT_KEY not in ctx

    async def test_forbidden_stack_marks_ctx(self) -> None:
        factory = make_factory()
        factory.access_validator = MagicMock(is_allowed=AsyncMock(return_value=False))
        ctx = make_ctx()

        await factory.process_message(make_message_created(), ctx, AsyncMock())  # type: ignore[arg-type]

        assert ctx[FORBIDDEN_STACK_KEY] is True
        assert STORAGE_KEY not in ctx


class TestIntentErrorMiddleware:
    def make(self) -> IntentErrorMiddleware:
        registry = MagicMock()
        registry.states_groups.return_value = {"SG": SG}
        return IntentErrorMiddleware(
            registry=registry,
            access_validator=DefaultAccessValidator(),
            events_isolation=make_isolation(),
        )

    def test_is_error_supported(self) -> None:
        event = MagicMock()
        event.update.update = make_message_created()

        assert self.make()._is_error_supported(event, make_ctx()) is True  # type: ignore[arg-type]

    def test_invalid_stack_id_error_not_supported(self) -> None:
        event = MagicMock()
        event.update.update = InvalidStackIdError("no")

        assert self.make()._is_error_supported(event, make_ctx()) is False  # type: ignore[arg-type]

    def test_unsupported_update_type(self) -> None:
        event = MagicMock()
        event.update.update = object()

        assert self.make()._is_error_supported(event, make_ctx()) is False  # type: ignore[arg-type]

    def test_without_update_context(self) -> None:
        event = MagicMock()
        event.update.update = make_message_created()
        ctx = make_ctx()
        del ctx[UPDATE_CONTEXT_KEY]

        assert self.make()._is_error_supported(event, ctx) is False  # type: ignore[arg-type]

    def test_without_event_from_user(self) -> None:
        event = MagicMock()
        event.update.update = make_message_created()
        ctx = make_ctx()
        del ctx[EVENT_FROM_USER_KEY]

        assert self.make()._is_error_supported(event, ctx) is False  # type: ignore[arg-type]

    async def test_skips_unsupported_error(self) -> None:
        event = MagicMock()
        event.update.update = object()
        next_ = AsyncMock(return_value="skipped")

        assert await self.make()(event, make_ctx(), next_) == "skipped"  # type: ignore[arg-type]

    async def test_fix_broken_stack_drops_all_contexts(self) -> None:
        storage = MagicMock(
            remove_context=AsyncMock(),
            save_stack=AsyncMock(),
        )
        stack = Stack()
        stack.push(SG.first, {})
        stack.push(SG.first, {})

        await self.make()._fix_broken_stack(storage, stack)

        assert stack.empty()
        assert storage.remove_context.await_count == 2
        storage.save_stack.assert_awaited_once()

    async def test_load_last_context_resets_broken_stack(self) -> None:
        stack = Stack()
        stack.push(SG.first, {})
        storage = MagicMock(
            load_context=AsyncMock(side_effect=UnknownIntent("gone")),
            remove_context=AsyncMock(),
            save_stack=AsyncMock(),
            user_id=1,
            chat_id=10,
        )

        assert await self.make()._load_last_context(storage, stack) is None
        assert stack.empty()

    async def test_load_last_context_returns_context(self) -> None:
        stack = Stack()
        stack.push(SG.first, {})
        context = MagicMock()
        storage = MagicMock(load_context=AsyncMock(return_value=context))

        assert await self.make()._load_last_context(storage, stack) is context

    async def test_load_stack_uses_stack_id_from_outdated_intent(self) -> None:
        proxy = MagicMock(load_stack=AsyncMock(return_value=Stack()))

        await self.make()._load_stack(proxy, OutdatedIntent("sid", "text"))

        proxy.load_stack.assert_awaited_once_with(stack_id="sid")

    async def test_load_stack_without_outdated_intent(self) -> None:
        proxy = MagicMock(load_stack=AsyncMock(return_value=Stack()))

        await self.make()._load_stack(proxy, RuntimeError("boom"))

        proxy.load_stack.assert_awaited_once_with()


class TestErrorPaths:
    async def test_load_context_by_stack_without_stack(self) -> None:
        proxy = MagicMock(
            load_stack=AsyncMock(return_value=None),
            user_id=1,
            chat_id=10,
        )
        ctx: dict[Any, Any] = {}

        await make_factory()._load_context_by_stack(
            event=make_message_created(),
            proxy=proxy,
            stack_id=DEFAULT_STACK_ID,
            ctx=ctx,  # type: ignore[arg-type]
        )

        assert STORAGE_KEY not in ctx

    async def test_load_context_by_stack_unlocks_on_load_error(self) -> None:
        stack = Stack()
        stack.push(SG.first, {})
        proxy = MagicMock(
            load_stack=AsyncMock(return_value=stack),
            load_context=AsyncMock(side_effect=UnknownIntent("gone")),
            unlock=AsyncMock(),
            user_id=1,
            chat_id=10,
        )

        with pytest.raises(UnknownIntent):
            await make_factory()._load_context_by_stack(
                event=make_message_created(),
                proxy=proxy,
                stack_id=DEFAULT_STACK_ID,
                ctx={},  # type: ignore[arg-type]
            )

        proxy.unlock.assert_awaited_once()

    async def test_load_context_by_intent_without_stack(self) -> None:
        proxy = MagicMock(
            load_context=AsyncMock(return_value=MagicMock(stack_id="sid")),
            load_stack=AsyncMock(return_value=None),
            user_id=1,
            chat_id=10,
        )
        ctx: dict[Any, Any] = {}

        await make_factory()._load_context_by_intent(
            event=make_message_created(),
            proxy=proxy,
            intent_id="intent",
            ctx=ctx,  # type: ignore[arg-type]
        )

        assert STORAGE_KEY not in ctx

    async def test_load_context_by_intent_unlocks_on_outdated(self) -> None:
        proxy = MagicMock(
            load_context=AsyncMock(return_value=MagicMock(stack_id="sid")),
            load_stack=AsyncMock(return_value=Stack()),
            unlock=AsyncMock(),
            user_id=1,
            chat_id=10,
        )

        with pytest.raises(OutdatedIntent):
            await make_factory()._load_context_by_intent(
                event=make_message_created(),
                proxy=proxy,
                intent_id="intent",
                ctx={},  # type: ignore[arg-type]
            )

        proxy.unlock.assert_awaited_once()

    async def test_load_context_by_intent_forbidden_stack(self) -> None:
        stack = Stack()
        context = stack.push(SG.first, {})
        proxy = MagicMock(
            load_context=AsyncMock(return_value=context),
            load_stack=AsyncMock(return_value=stack),
            unlock=AsyncMock(),
            user_id=1,
            chat_id=10,
        )
        factory = make_factory()
        factory.access_validator = MagicMock(is_allowed=AsyncMock(return_value=False))
        ctx: dict[Any, Any] = {}

        await factory._load_context_by_intent(
            event=make_message_created(),
            proxy=proxy,
            intent_id=stack.last_intent_id(),
            ctx=ctx,  # type: ignore[arg-type]
        )

        assert ctx[FORBIDDEN_STACK_KEY] is True
        assert STORAGE_KEY not in ctx

    async def test_process_callback_without_payload(self) -> None:
        ctx = make_ctx()
        update = make_message_callback()
        update.callback.payload = Omitted()

        await make_factory().process_callback(update, ctx, AsyncMock())  # type: ignore[arg-type]

        assert PAYLOAD_KEY not in ctx
        assert ctx[STORAGE_KEY] is not None

    async def test_error_middleware_marks_forbidden_stack(self) -> None:
        registry = MagicMock()
        registry.states_groups.return_value = {"SG": SG}
        middleware = IntentErrorMiddleware(
            registry=registry,
            access_validator=MagicMock(is_allowed=AsyncMock(return_value=False)),
            events_isolation=make_isolation(),
        )
        event = MagicMock()
        event.update.update = make_message_created()
        event.event = make_message_created()
        event.error = RuntimeError("boom")
        ctx = make_ctx()

        await middleware(event, ctx, AsyncMock(return_value="ok"))  # type: ignore[arg-type]

        assert ctx[FORBIDDEN_STACK_KEY] is True
        assert STACK_KEY not in ctx
