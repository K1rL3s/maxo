from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import Bot
from maxo.enums import ChatType, MessageLinkType
from maxo.omit import Omitted
from maxo.types import (
    CallbackButton,
    Message,
    MessageBody,
    Recipient,
    SendMessageResult,
    SimpleQueryResult,
    User,
)
from maxo.types.facades import MessageMethodsFacade
from tests.constants import NOW


class MockMessageFacade(MessageMethodsFacade):
    def __init__(self, bot: Bot, message: Message) -> None:
        self._bot = bot
        self._message = message

    @property
    def message(self) -> Message:
        return self._message


def make_message(
    chat_type: ChatType = ChatType.DIALOG,
    with_sender: bool = True,
    text: str | None = "hi",
) -> Message:
    kwargs: dict[str, Any] = {}
    if with_sender:
        kwargs["sender"] = User(
            user_id=5,
            is_bot=False,
            first_name="U",
            last_activity_time=NOW,
        )
    return Message(
        timestamp=NOW,
        recipient=Recipient(chat_type=chat_type, chat_id=10, user_id=5),
        body=MessageBody(mid="m1", seq=1, text=text),
        **kwargs,
    )


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
    bot.get_message_by_id = AsyncMock(return_value=sent)
    return bot


@pytest.fixture
def facade(bot: MagicMock) -> MockMessageFacade:
    return MockMessageFacade(bot, make_message())


def test_chat_id_comes_from_recipient(facade: MockMessageFacade) -> None:
    assert facade.chat_id == 10


async def test_delete_message(facade: MockMessageFacade, bot: MagicMock) -> None:
    await facade.delete_message()

    bot.delete_message.assert_awaited_once_with(message_id="m1")


async def test_get_message_by_id(facade: MockMessageFacade, bot: MagicMock) -> None:
    await facade.get_message_by_id("m2")

    bot.get_message_by_id.assert_awaited_once_with(message_id="m2")


class TestSendMessage:
    async def test_dialog_passes_chat_and_user(
        self,
        facade: MockMessageFacade,
        bot: MagicMock,
    ) -> None:
        result = await facade.send_message("hello")

        kwargs = bot.send_message.await_args.kwargs
        assert kwargs["chat_id"] == 10
        assert kwargs["user_id"] == 5
        assert result.body.text == "sent"

    async def test_chat_omits_user_id(self, bot: MagicMock) -> None:
        facade = MockMessageFacade(bot, make_message(chat_type=ChatType.CHAT))

        await facade.send_message("hello")

        assert bot.send_message.await_args.kwargs["user_id"] == Omitted()

    async def test_without_sender(self, bot: MagicMock) -> None:
        facade = MockMessageFacade(bot, make_message(with_sender=False))

        await facade.send_message("hello")

        assert bot.send_message.await_args.kwargs["user_id"] == Omitted()

    async def test_answer_is_alias(self, facade: MockMessageFacade) -> None:
        assert facade.answer.__func__ is facade.send_message.__func__  # type: ignore[attr-defined]


class TestReply:
    async def test_reply_adds_link(
        self,
        facade: MockMessageFacade,
        bot: MagicMock,
    ) -> None:
        await facade.reply("hello")

        link = bot.send_message.await_args.kwargs["link"]
        assert link.type is MessageLinkType.REPLY
        assert link.mid == "m1"

    async def test_reply_text(self, facade: MockMessageFacade, bot: MagicMock) -> None:
        await facade.reply_text("hello")

        assert bot.send_message.await_args.kwargs["link"] is not None

    async def test_answer_text(self, facade: MockMessageFacade, bot: MagicMock) -> None:
        await facade.answer_text("hello")

        assert bot.send_message.await_args.kwargs["text"] == "hello"


class TestSendMedia:
    async def test_send_media_builds_attachments(
        self,
        facade: MockMessageFacade,
        bot: MagicMock,
    ) -> None:
        await facade.send_media(media=[], text="caption")

        assert bot.send_message.await_args.kwargs["text"] == "caption"


class TestEditMessage:
    async def test_keeps_text_when_not_given(
        self,
        facade: MockMessageFacade,
        bot: MagicMock,
    ) -> None:
        await facade.edit_message()

        kwargs = bot.edit_message.await_args.kwargs
        assert kwargs["text"] == "hi"
        assert kwargs["attachments"] is None

    async def test_builds_attachments_for_keyboard(
        self,
        facade: MockMessageFacade,
        bot: MagicMock,
    ) -> None:
        await facade.edit_message(
            text="new",
            keyboard=[[CallbackButton(text="b", payload="p")]],
        )

        kwargs = bot.edit_message.await_args.kwargs
        assert kwargs["text"] == "new"
        assert kwargs["attachments"]

    async def test_make_new_message_link(self, facade: MockMessageFacade) -> None:
        link = facade._make_new_message_link(MessageLinkType.FORWARD)

        assert link.type is MessageLinkType.FORWARD
        assert link.mid == "m1"
