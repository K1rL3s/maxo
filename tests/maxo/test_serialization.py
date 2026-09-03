import pytest
from adaptix.load_error import LoadError

from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import (
    AnswerOnCallback,
    EditMessage,
    GetMembers,
    GetMessages,
    GetUpdates,
    SendMessage,
)
from maxo.enums import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_omitted
from maxo.serialization import get_retort
from maxo.types import (
    CommentCreated,
    CommentEdited,
    CommentMessage,
    CommentRemoved,
    Message,
    MessageCreated,
    NewMessageBody,
    UpdateList,
)
from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin, bind_bot
from tests.factories import make_bot


class Sub(MaxoType, BotMixin):
    b: int


class MyType(MaxoType, BotMixin):
    a: str
    sub: Sub


@pytest.mark.parametrize(
    "default",
    [TextFormat.HTML, TextFormat.MARKDOWN, None, Omitted()],
)
def test_bot_default_text_format(default: Omittable[TextFormat | None]) -> None:
    defaults = BotDefaults(text_format=default)
    retort = get_retort()

    data = retort.dump(apply_defaults(SendMessage(), defaults))
    if is_omitted(default):
        assert "format" not in data["body"]
    else:
        assert data["body"]["format"] == default

    data = retort.dump(apply_defaults(EditMessage(message_id="1"), defaults))
    if is_omitted(default):
        assert "format" not in data["body"]
    else:
        assert data["body"]["format"] == default

    # `NewMessageBody` сверху не дампится - только внутри `AnswerOnCallback`,
    # где `apply_defaults` спускается в него отдельно.
    data = retort.dump(
        apply_defaults(
            AnswerOnCallback(callback_id="c", message=NewMessageBody()),
            defaults,
        ),
    )
    if is_omitted(default):
        assert "format" not in data["body"]["message"]
    else:
        assert data["body"]["message"]["format"] == default


@pytest.mark.parametrize(
    "default",
    [True, False, Omitted()],
)
def test_bot_default_disable_link_preview(default: Omittable[bool]) -> None:
    defaults = BotDefaults(disable_link_preview=default)
    retort = get_retort()

    data = retort.dump(apply_defaults(SendMessage(), defaults))
    if is_omitted(default):
        assert "disable_link_preview" not in data["query"]
    else:
        assert data["query"]["disable_link_preview"] == default


@pytest.mark.parametrize(
    "method",
    [
        GetUpdates(marker=None),
        GetUpdates(types=None),
        GetMessages(message_ids=None),
        GetMembers(chat_id=1, user_ids=None),
    ],
)
def test_query_none_is_omitted(method: object) -> None:
    retort = get_retort()

    data = retort.dump(method)

    assert not data.get("query")


def test_bind_binds_whole_tree() -> None:
    bot = make_bot(token="")
    retort = get_retort()

    data = {"a": "a", "sub": {"b": 1}}
    my = bind_bot(retort.load(data, MyType), bot)

    assert bot is my.bot is my.sub.bot

    dump = retort.dump(my, MyType)
    assert dump == data


def test_retort_without_bot_no_load_bot() -> None:
    retort = get_retort()

    data = {"a": "a", "sub": {"b": 1}}

    my = retort.load(data, MyType)

    with pytest.raises(AttributeIsEmptyError):
        _ = my.bot

    with pytest.raises(AttributeIsEmptyError):
        _ = my.sub.bot

    dump = retort.dump(my, MyType)
    assert dump == data


def test_retort_empty_message() -> None:
    retort = get_retort()

    data = {
        "marker": 1,
        "updates": [
            {
                "update_type": "message_created",
                "timestamp": 1234567890,
                "user_locale": "ru",
            },
        ],
    }

    with pytest.raises(LoadError):
        _ = retort.load(data, UpdateList)


def test_retort_full_message_created_loads_ok() -> None:
    retort = get_retort()

    # Полный валидный message_created - убеждаемся, что регрессия не сломала happy path
    data = {
        "marker": 1,
        "updates": [
            {
                "update_type": "message_created",
                "timestamp": 1234567890,
                "user_locale": "ru",
                "message": {
                    "body": {"seq": 1, "mid": "msg-1", "text": "hello"},
                    "recipient": {"chat_id": 1, "chat_type": "dialog"},
                    "timestamp": 1234567890,
                },
            },
        ],
    }

    result = retort.load(data, UpdateList)
    assert len(result.updates) == 1


def test_retort_keeps_message_created_with_post_id_as_message() -> None:
    retort = get_retort()
    data = {
        "marker": 1,
        "updates": [
            {
                "update_type": "message_created",
                "timestamp": 1234567890,
                "message": {
                    "body": {"seq": 1, "mid": "comment", "text": "hello"},
                    "recipient": {
                        "chat_id": 1,
                        "chat_type": "channel",
                        "post_id": "post",
                    },
                    "timestamp": 1234567890,
                },
            },
            {
                "update_type": "message_created",
                "timestamp": 1234567890,
                "message": {
                    "body": {"seq": 2, "mid": "message", "text": "hello"},
                    "recipient": {
                        "chat_id": 1,
                        "chat_type": "channel",
                    },
                    "timestamp": 1234567890,
                },
            },
        ],
    }

    result = retort.load(data, UpdateList)
    comment_update, message_update = result.updates

    assert isinstance(comment_update, MessageCreated)
    assert isinstance(message_update, MessageCreated)
    assert type(comment_update.message) is Message
    assert type(message_update.message) is Message


def test_retort_loads_comment_updates_from_raw_json() -> None:
    retort = get_retort()
    comment = {
        "body": {"seq": 1, "mid": "comment", "text": "hello"},
        "recipient": {
            "chat_id": 1,
            "chat_type": "channel",
            "post_id": "post",
        },
        "timestamp": 1234567890,
    }
    data = {
        "marker": 1,
        "updates": [
            {
                "update_type": "comment_created",
                "timestamp": 1234567890,
                "message": comment,
            },
            {
                "update_type": "comment_edited",
                "timestamp": 1234567890,
                "message": comment,
            },
            {
                "update_type": "comment_removed",
                "timestamp": 1234567890,
                "chat_id": 1,
                "message_id": "comment",
                "post_id": "post",
                "user_id": 2,
            },
        ],
    }

    result = retort.load(data, UpdateList)

    assert isinstance(result.updates[0], CommentCreated)
    assert isinstance(result.updates[0].message, CommentMessage)
    assert isinstance(result.updates[1], CommentEdited)
    assert isinstance(result.updates[1].message, CommentMessage)
    assert isinstance(result.updates[2], CommentRemoved)
