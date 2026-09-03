from datetime import UTC, datetime

import pytest
from unihttp.bind_method import MethodBinder

from maxo import Bot
from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import (
    DeleteComment,
    EditComment,
    GetCommentById,
    GetComments,
    SendComment,
)
from maxo.enums import TextFormat
from maxo.serialization import get_retort
from maxo.types import (
    CommentMessage,
    CommentMessageList,
    NewCommentBody,
    SendCommentResult,
    SimpleQueryResult,
)


def test_wire_contracts() -> None:
    assert GetComments.__url__ == "messages/{message_id}/comments"
    assert GetComments.__method__ == "get"
    assert GetComments.__returning__ is CommentMessageList
    assert SendComment.__url__ == "messages/{message_id}/comments"
    assert SendComment.__method__ == "post"
    assert SendComment.__returning__ is SendCommentResult
    assert EditComment.__url__ == "messages/{message_id}/comments"
    assert EditComment.__method__ == "put"
    assert EditComment.__returning__ is SimpleQueryResult
    assert DeleteComment.__url__ == "messages/{message_id}/comments"
    assert DeleteComment.__method__ == "delete"
    assert DeleteComment.__returning__ is SimpleQueryResult
    assert GetCommentById.__url__ == "messages/{message_id}/comments/{comment_id}"
    assert GetCommentById.__method__ == "get"
    assert GetCommentById.__returning__ is CommentMessage


def test_bot_exposes_comment_methods() -> None:
    assert isinstance(Bot.delete_comment, MethodBinder)
    assert isinstance(Bot.edit_comment, MethodBinder)
    assert isinstance(Bot.get_comment_by_id, MethodBinder)
    assert isinstance(Bot.get_comments, MethodBinder)
    assert isinstance(Bot.send_comment, MethodBinder)


def test_dump() -> None:
    retort = get_retort()
    defaults = BotDefaults()

    assert retort.dump(GetComments(message_id="post")) == {
        "path": {"message_id": "post"},
        "query": {},
    }
    assert retort.dump(
        apply_defaults(
            SendComment(message_id="post", text="Текст"),
            defaults,
        ),
    ) == {
        "path": {"message_id": "post"},
        "query": {},
        "body": {"format": None, "link": None, "text": "Текст"},
    }
    assert retort.dump(
        apply_defaults(
            EditComment(message_id="post", comment_id="comment"),
            defaults,
        ),
    ) == {
        "path": {"message_id": "post"},
        "query": {"comment_id": "comment"},
        "body": {"format": None, "link": None, "text": None},
    }
    assert retort.dump(DeleteComment(message_id="post", comment_id="comment")) == {
        "path": {"message_id": "post"},
        "query": {"comment_id": "comment"},
    }
    assert retort.dump(GetCommentById(message_id="post", comment_id="comment")) == {
        "path": {"message_id": "post", "comment_id": "comment"},
    }


def test_dump_datetime_query_as_milliseconds() -> None:
    retort = get_retort()

    assert (
        retort.dump(
            GetComments(
                message_id="post",
                after=datetime(2026, 8, 17, 17, 25, 6, 123000, tzinfo=UTC),
            ),
        )["query"]["after"]
        == 1_786_987_506_123
    )


@pytest.mark.parametrize(
    "method",
    [
        SendComment(message_id="post"),
        EditComment(message_id="post", comment_id="comment"),
        NewCommentBody(),
    ],
)
def test_comment_body_uses_bot_defaults(method: object) -> None:
    defaults = BotDefaults(
        text_format=TextFormat.MARKDOWN,
        disable_link_preview=True,
    )
    retort = get_retort()

    data = retort.dump(apply_defaults(method, defaults))
    body = data.get("body", data)

    assert body["format"] == "markdown"
    if isinstance(method, SendComment):
        assert data["query"]["disable_link_preview"] == 1


def test_comment_message_loads_null_sender() -> None:
    retort = get_retort()
    raw = {
        "sender": None,
        "recipient": {
            "chat_type": "channel",
            "chat_id": 10,
            "user_id": None,
            "post_id": "post",
        },
        "timestamp": 0,
        "body": {
            "mid": "comment",
            "seq": 1,
            "text": "Текст",
        },
    }

    comment = retort.load(raw, CommentMessage)

    assert comment.sender is None
