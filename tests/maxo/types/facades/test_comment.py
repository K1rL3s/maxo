import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.enums import ChatType, MessageLinkType
from maxo.omit import is_omitted
from maxo.types import (
    CommentCreated,
    CommentEdited,
    CommentMessage,
    CommentMessageBody,
    Message,
    MessageCreated,
    NewMessageLink,
    Recipient,
    SendCommentResult,
    SimpleQueryResult,
)
from maxo.types.facades.comment import CommentMethodsFacade
from maxo.types.facades.message import MessageMethodsFacade
from tests.constants import NOW


def make_comment() -> CommentMessage:
    return CommentMessage(
        body=CommentMessageBody(mid="comment", seq=1, text="old"),
        recipient=Recipient(
            chat_type=ChatType.CHANNEL,
            chat_id=1,
            post_id="post",
        ),
        timestamp=NOW,
    )


def make_bot(comment: CommentMessage) -> MagicMock:
    bot = MagicMock()
    bot.send_comment = AsyncMock(return_value=SendCommentResult(message=comment))
    bot.edit_comment = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.delete_comment = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.get_comment_by_id = AsyncMock(return_value=comment)
    return bot


async def test_unsupported_parameters_are_warned_and_ignored(
    caplog: pytest.LogCaptureFixture,
) -> None:
    comment = make_comment()
    bot = make_bot(comment)
    comment.as_(bot)

    with caplog.at_level(logging.WARNING, logger="maxo.utils"):
        result = await comment.send_message(
            text="new",
            link=NewMessageLink(type=MessageLinkType.FORWARD, mid="source"),
            notify=False,
            keyboard=[],
            attachments=[],
        )

    assert result is comment
    kwargs = bot.send_comment.await_args.kwargs
    assert kwargs["message_id"] == "post"
    assert kwargs["text"] == "new"
    assert kwargs["link"] is None
    assert is_omitted(kwargs["format"])
    assert is_omitted(kwargs["disable_link_preview"])
    assert len(caplog.records) == 1


async def test_reply_link_is_passed_to_comment_api() -> None:
    comment = make_comment()
    bot = make_bot(comment)
    comment.as_(bot)
    link = NewMessageLink(type=MessageLinkType.REPLY, mid="source")

    await comment.edit_message(link=link)

    assert bot.edit_comment.await_args.kwargs["link"] is link


async def test_edit_ignores_unsupported_parameters(
    caplog: pytest.LogCaptureFixture,
) -> None:
    comment = make_comment()
    bot = make_bot(comment)
    comment.as_(bot)

    with caplog.at_level(logging.WARNING, logger="maxo.utils"):
        await comment.edit_message(
            link=NewMessageLink(type=MessageLinkType.FORWARD, mid="source"),
            notify=False,
            media=[],
        )

    assert bot.edit_comment.await_args.kwargs["link"] is None
    assert len(caplog.records) == 1


async def test_message_facade_redispatches_to_comment() -> None:
    comment = make_comment()
    bot = make_bot(comment)
    update = MessageCreated(message=comment, timestamp=NOW).as_(bot)

    await update.send_message("new")
    await update.edit_message("edited")
    await update.delete_message()
    result = await update.get_message_by_id("other")

    bot.send_comment.assert_awaited_once()
    bot.edit_comment.assert_awaited_once()
    bot.delete_comment.assert_awaited_once_with(
        message_id="post",
        comment_id="comment",
    )
    bot.get_comment_by_id.assert_awaited_once_with(
        message_id="post",
        comment_id="other",
    )
    assert result is comment


@pytest.mark.parametrize("update_type", [CommentCreated, CommentEdited])
async def test_comment_update_answer_uses_comment_api(
    update_type: type[CommentCreated | CommentEdited],
) -> None:
    comment = make_comment()
    bot = make_bot(comment)
    comment.as_(bot)
    update = update_type(message=comment, timestamp=NOW).as_(bot)

    result = await update.message.answer("new")

    bot.send_comment.assert_awaited_once()
    bot.send_message.assert_not_called()
    assert result is comment


def test_comment_method_aliases() -> None:
    assert issubclass(CommentMessage, Message)
    assert issubclass(CommentMessage, MessageMethodsFacade)
    assert CommentMethodsFacade.send_comment is CommentMethodsFacade.send_message
    assert CommentMethodsFacade.edit_comment is CommentMethodsFacade.edit_message
    assert CommentMethodsFacade.delete_comment is CommentMethodsFacade.delete_message
    assert (
        CommentMethodsFacade.get_comment_by_id is CommentMethodsFacade.get_message_by_id
    )
