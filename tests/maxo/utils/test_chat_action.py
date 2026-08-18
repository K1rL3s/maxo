import asyncio
import time
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest

from maxo import Bot
from maxo.enums import ChatType, SenderAction
from maxo.routing.ctx import Ctx
from maxo.routing.flags import HANDLER_KEY, flags
from maxo.routing.handlers.update import UpdateHandler
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.types import (
    Callback,
    Message,
    MessageBody,
    MessageCallback,
    MessageCreated,
    Recipient,
    UpdateContext,
    User,
)
from maxo.utils.chat_action import (
    DEFAULT_INITIAL_SLEEP,
    DEFAULT_INTERVAL,
    ChatActionMiddleware,
    ChatActionSender,
)
from tests.constants import NOW
from tests.factories import make_flagged_handler

CHAT_ID = 42


def make_update(chat_id: int | None = CHAT_ID) -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text="hello"),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=chat_id),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
    )


def make_user() -> User:
    return User(
        user_id=1,
        first_name="Test",
        is_bot=False,
        last_activity_time=NOW,
    )


def make_callback_update(chat_id: int | None = CHAT_ID) -> MessageCallback:
    message = (
        None
        if chat_id is None
        else Message(
            body=MessageBody(mid="test", seq=1, text="hello"),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=chat_id),
            timestamp=NOW,
            sender=make_user(),
        )
    )
    return MessageCallback(
        timestamp=NOW,
        callback=Callback(callback_id="cb", timestamp=NOW, user=make_user()),
        message=message,
    )


def make_ctx(update: Any, bot: Any, **extra: Any) -> Ctx:
    return Ctx({"update": update, "bot": bot, **extra})


def make_ctx_with_flags(update: Any, bot: Any, **handler_flags: Any) -> Ctx:
    return make_ctx(update, bot, **{HANDLER_KEY: make_flagged_handler(**handler_flags)})


async def _next_slow(ctx: Ctx) -> str:
    await asyncio.sleep(0.05)
    return "OK"


async def _next_ok(ctx: Ctx) -> str:
    return "OK"


@pytest.fixture
def bot() -> AsyncMock:
    return AsyncMock()


class TestChatActionSender:
    def test_defaults(self, bot: AsyncMock) -> None:
        sender = ChatActionSender(bot=cast(Bot, bot), chat_id=CHAT_ID)

        assert sender.chat_id == CHAT_ID
        assert sender.action == SenderAction.TYPING_ON
        assert sender.interval == DEFAULT_INTERVAL
        assert sender.initial_sleep == DEFAULT_INITIAL_SLEEP
        assert sender.bot is bot
        assert sender.running is False

    @pytest.mark.parametrize(
        "action",
        [
            SenderAction.TYPING_ON,
            SenderAction.SENDING_PHOTO,
            SenderAction.SENDING_VIDEO,
            SenderAction.SENDING_AUDIO,
            SenderAction.SENDING_FILE,
            SenderAction.MARK_SEEN,
        ],
    )
    def test_factories(self, action: SenderAction, bot: AsyncMock) -> None:
        sender_factory = getattr(ChatActionSender, action.value)
        sender = sender_factory(chat_id=CHAT_ID, bot=cast(Bot, bot))

        assert isinstance(sender, ChatActionSender)
        assert sender.action == action
        assert sender.chat_id == CHAT_ID
        assert sender.bot is bot

    async def test_wait_is_interrupted_by_close_event(self, bot: AsyncMock) -> None:
        sender = ChatActionSender.typing_on(bot=cast(Bot, bot), chat_id=CHAT_ID)
        asyncio.get_running_loop().call_soon(sender._close_event.set)

        start = time.monotonic()
        await sender._wait(5)

        assert time.monotonic() - start < 5

    async def test_worker_sends_actions(self, bot: AsyncMock) -> None:
        async with ChatActionSender.typing_on(
            bot=cast(Bot, bot),
            chat_id=CHAT_ID,
            interval=0.01,
            initial_sleep=0,
        ):
            await asyncio.sleep(0.1)

            assert bot.send_action.await_count > 1
            bot.send_action.assert_awaited_with(
                chat_id=CHAT_ID,
                action=SenderAction.TYPING_ON,
            )

    async def test_context_manager(self, bot: AsyncMock) -> None:
        sender = ChatActionSender.typing_on(bot=cast(Bot, bot), chat_id=CHAT_ID)
        states: list[bool] = [sender.running]

        await sender._stop()
        states.append(sender.running)

        async with sender:
            states.append(sender.running)
            assert not sender._close_event.is_set()

            with pytest.raises(RuntimeError):
                await sender._run()

        states.append(sender.running)

        assert states == [False, False, True, False]

    async def test_initial_sleep_delays_first_action(self, bot: AsyncMock) -> None:
        async with ChatActionSender.typing_on(
            bot=cast(Bot, bot),
            chat_id=CHAT_ID,
            interval=0.01,
            initial_sleep=5,
        ):
            await asyncio.sleep(0.05)

            bot.send_action.assert_not_awaited()


class TestChatActionMiddleware:
    async def test_typing_by_default(self, bot: AsyncMock) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        assert await middleware(update, ctx, _next_slow) == "OK"
        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.TYPING_ON,
        )

    @pytest.mark.parametrize(
        "flag_value",
        ["sending_photo", SenderAction.SENDING_PHOTO],
    )
    async def test_action_from_flag(
        self,
        flag_value: Any,
        bot: AsyncMock,
    ) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot, chat_action=flag_value)
        middleware = ChatActionMiddleware()

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.SENDING_PHOTO,
        )

    async def test_bool_flag_falls_back_to_typing(self, bot: AsyncMock) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot, chat_action=True)
        middleware = ChatActionMiddleware()

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.TYPING_ON,
        )

    @pytest.mark.parametrize("flag_value", [False, None])
    async def test_falsy_flag_disables_sender(
        self,
        flag_value: Any,
        bot: AsyncMock,
    ) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot, chat_action=flag_value)
        middleware = ChatActionMiddleware()

        assert await middleware(update, ctx, _next_slow) == "OK"
        bot.send_action.assert_not_awaited()

    async def test_middleware_defaults_used_without_flag(self, bot: AsyncMock) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware(action=SenderAction.SENDING_FILE)

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.SENDING_FILE,
        )

    async def test_flag_overrides_middleware_defaults(self, bot: AsyncMock) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot, chat_action="sending_photo")
        middleware = ChatActionMiddleware(action=SenderAction.SENDING_FILE)

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.SENDING_PHOTO,
        )

    async def test_middleware_initial_sleep_skips_short_handlers(
        self,
        bot: AsyncMock,
    ) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware(initial_sleep=5)

        assert await middleware(update, ctx, _next_slow) == "OK"
        bot.send_action.assert_not_awaited()

    async def test_dict_flag_configures_sender(self, bot: AsyncMock) -> None:
        @flags.chat_action(action="sending_file", interval=0.01, initial_sleep=0)
        async def stub(update: MessageCreated) -> None:
            pass

        update = make_update()
        ctx = make_ctx(update, bot, **{HANDLER_KEY: UpdateHandler(stub)})
        middleware = ChatActionMiddleware()

        await middleware(update, ctx, _next_slow)

        assert bot.send_action.await_count > 1
        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.SENDING_FILE,
        )

    async def test_skips_without_chat_id(self, bot: AsyncMock) -> None:
        update = make_update(chat_id=None)
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        assert await middleware(update, ctx, _next_ok) == "OK"
        bot.send_action.assert_not_awaited()

    async def test_chat_id_from_update_context(self, bot: AsyncMock) -> None:
        update = make_update(chat_id=None)
        ctx = make_ctx_with_flags(update, bot)
        ctx[UPDATE_CONTEXT_KEY] = UpdateContext(chat_id=CHAT_ID, user_id=1)
        middleware = ChatActionMiddleware()

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.TYPING_ON,
        )

    async def test_chat_id_from_message_callback(self, bot: AsyncMock) -> None:
        update = make_callback_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        await middleware(update, ctx, _next_slow)

        bot.send_action.assert_awaited_with(
            chat_id=CHAT_ID,
            action=SenderAction.TYPING_ON,
        )

    async def test_skips_message_callback_without_message(
        self,
        bot: AsyncMock,
    ) -> None:
        update = make_callback_update(chat_id=None)
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        assert await middleware(update, ctx, _next_ok) == "OK"
        bot.send_action.assert_not_awaited()

    async def test_sender_survives_send_action_error(self, bot: AsyncMock) -> None:
        bot.send_action.side_effect = RuntimeError("api is down")
        update = make_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        assert await middleware(update, ctx, _next_slow) == "OK"
        bot.send_action.assert_awaited()

    async def test_stops_after_handler_error(self, bot: AsyncMock) -> None:
        update = make_update()
        ctx = make_ctx_with_flags(update, bot)
        middleware = ChatActionMiddleware()

        async def next_fn(ctx: Ctx) -> str:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            await middleware(update, ctx, next_fn)
