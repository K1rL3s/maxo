from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.enums import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omitted
from maxo.types import (
    Message,
    MessageBody,
    MessageCallback,
    NewMessageBody,
    Recipient,
    SendMessageResult,
    SimpleQueryResult,
)
from tests.constants import NOW

from .conftest import make_callback, make_message, make_user


@pytest.fixture
def bot() -> MagicMock:
    sent = Message(
        timestamp=NOW,
        recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=5),
        body=MessageBody(mid="m2", seq=2, text="sent"),
    )
    bot = MagicMock()
    bot.send_message = AsyncMock(return_value=SendMessageResult(message=sent))
    bot.edit_message = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.delete_message = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.answer_on_callback = AsyncMock(return_value=SimpleQueryResult(success=True))
    return bot


@pytest.fixture
def callback_without_message(bot: MagicMock) -> MessageCallback:
    update = MessageCallback(callback=make_callback(), message=None, timestamp=NOW)
    update.as_(bot)
    return update


class TestMessageCallbackWithoutMessage:
    def test_chat_id_raises_attribute_is_empty(
        self,
        callback_without_message: MessageCallback,
    ) -> None:
        with pytest.raises(AttributeIsEmptyError):
            _ = callback_without_message.chat_id

    async def test_delete_message_raises_attribute_is_empty(
        self,
        callback_without_message: MessageCallback,
    ) -> None:
        with pytest.raises(AttributeIsEmptyError):
            await callback_without_message.delete_message()

    async def test_send_message_raises_attribute_is_empty(
        self,
        callback_without_message: MessageCallback,
    ) -> None:
        with pytest.raises(AttributeIsEmptyError):
            await callback_without_message.send_message("hi")

    async def test_reply_raises_attribute_is_empty(
        self,
        callback_without_message: MessageCallback,
    ) -> None:
        with pytest.raises(AttributeIsEmptyError):
            await callback_without_message.reply("hi")

    async def test_edit_message_raises_attribute_is_empty(
        self,
        callback_without_message: MessageCallback,
    ) -> None:
        with pytest.raises(AttributeIsEmptyError):
            await callback_without_message.edit_message("hi")

    async def test_callback_answer_works_without_message(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_without_message.callback_answer(notification="ok")

        bot.answer_on_callback.assert_awaited_once_with(
            callback_id="cb",
            notification="ok",
            message=None,
            disable_link_preview=Omitted(),
        )

    @pytest.mark.parametrize("notification", [Omitted(), None])
    async def test_callback_answer_sends_empty_notification_without_message(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
        notification: str | None | Omitted,
    ) -> None:
        await callback_without_message.callback_answer(notification=notification)

        assert bot.answer_on_callback.await_args.kwargs["notification"] == ""

    async def test_callback_answer_with_message_keeps_notification_omitted(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        message = NewMessageBody(text="edited")

        await callback_without_message.callback_answer(message=message)

        bot.answer_on_callback.assert_awaited_once_with(
            callback_id="cb",
            notification=Omitted(),
            message=message,
            disable_link_preview=Omitted(),
        )


class TestCallbackAnswer:
    """Ported from upstream `tests/maxo/types/facades/test_callback.py`."""

    async def test_forwards_all_params(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        message = NewMessageBody(text="edited")

        await callback_without_message.callback_answer(
            notification="Готово",
            message=message,
            disable_link_preview=True,
        )

        bot.answer_on_callback.assert_awaited_once_with(
            callback_id="cb",
            notification="Готово",
            message=message,
            disable_link_preview=True,
        )

    async def test_uses_text_alias(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_without_message.callback_answer(
            text="Готово",
            disable_link_preview=False,
        )

        bot.answer_on_callback.assert_awaited_once_with(
            callback_id="cb",
            notification="Готово",
            message=None,
            disable_link_preview=False,
        )

    async def test_prefers_notification_over_text(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_without_message.callback_answer(
            notification="Первое",
            text="Второе",
        )

        assert bot.answer_on_callback.await_args.kwargs["notification"] == "Первое"

    async def test_answer_alias_forwards_disable_link_preview(
        self,
        callback_without_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_without_message.answer(
            notification="Готово",
            disable_link_preview=True,
        )

        bot.answer_on_callback.assert_awaited_once_with(
            callback_id="cb",
            notification="Готово",
            message=None,
            disable_link_preview=True,
        )


class TestMessageCallbackWithMessage:
    @pytest.fixture
    def callback_with_message(self, bot: MagicMock) -> MessageCallback:
        update = MessageCallback(
            callback=make_callback(),
            # Личка: chat_id берётся из recipient, user_id - из sender.
            message=make_message(
                recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10),
                sender=make_user(),
            ),
            timestamp=NOW,
        )
        update.as_(bot)
        return update

    def test_chat_id_comes_from_recipient(
        self,
        callback_with_message: MessageCallback,
    ) -> None:
        assert callback_with_message.chat_id == 10

    async def test_send_message_passes_chat_id_and_user_id(
        self,
        callback_with_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_with_message.send_message("hello")

        assert bot.send_message.await_args.kwargs["chat_id"] == 10
        assert bot.send_message.await_args.kwargs["user_id"] == 1

    async def test_delete_message_uses_mid(
        self,
        callback_with_message: MessageCallback,
        bot: MagicMock,
    ) -> None:
        await callback_with_message.delete_message()

        bot.delete_message.assert_awaited_once_with(message_id="mid")
