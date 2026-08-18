import pytest
from adaptix.load_error import LoadError

from maxo.bot.defaults import BotDefaults
from maxo.bot.methods import (
    EditMessage,
    GetMembers,
    GetMessages,
    GetUpdates,
    SendMessage,
)
from maxo.enums import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_omitted
from maxo.serialization import create_retort, create_retort_with_bot
from maxo.types import NewMessageBody, UpdateList
from maxo.types.base import MaxoType
from tests.factories import make_bot


class Sub(MaxoType):
    b: int


class MyType(MaxoType):
    a: str
    sub: Sub


@pytest.mark.parametrize(
    "default",
    [TextFormat.HTML, TextFormat.MARKDOWN, None, Omitted()],
)
def test_bot_default_text_format(default: Omittable[TextFormat | None]) -> None:
    defaults = BotDefaults(text_format=default)
    retort = create_retort(defaults=defaults, warming_up=False)

    data = retort.dump(SendMessage())
    if is_omitted(default):
        assert "format" not in data["body"]
    else:
        assert data["body"]["format"] == default

    data = retort.dump(EditMessage(message_id="1"))
    if is_omitted(default):
        assert "format" not in data["body"]
    else:
        assert data["body"]["format"] == default

    data = retort.dump(NewMessageBody())
    if is_omitted(default):
        assert "format" not in data
    else:
        assert data["format"] == default


@pytest.mark.parametrize(
    "default",
    [True, False, Omitted()],
)
def test_bot_default_disable_link_preview(default: Omittable[bool]) -> None:
    defaults = BotDefaults(disable_link_preview=default)
    retort = create_retort(defaults=defaults, warming_up=False)

    data = retort.dump(SendMessage())
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
    retort = create_retort(warming_up=False)

    data = retort.dump(method)

    assert not data.get("query")


def test_retort_from_bot_load_bot() -> None:
    bot = make_bot(token="")
    retort = bot.retort

    data = {"a": "a", "sub": {"b": 1}}

    my = retort.load(data, MyType)
    assert bot is my.bot is my.sub.bot

    dump = retort.dump(my, MyType)
    assert dump == data


def test_retort_with_bot_load_bot() -> None:
    bot = make_bot(token="")
    retort = create_retort_with_bot(bot=bot, warming_up=False)

    data = {"a": "a", "sub": {"b": 1}}

    my = retort.load(data, MyType)
    assert bot is my.bot is my.sub.bot

    dump = retort.dump(my, MyType)
    assert dump == data


def test_retort_without_bot_no_load_bot() -> None:
    retort = create_retort(warming_up=False)

    data = {"a": "a", "sub": {"b": 1}}

    my = retort.load(data, MyType)

    with pytest.raises(AttributeIsEmptyError):
        _ = my.bot

    with pytest.raises(AttributeIsEmptyError):
        _ = my.sub.bot

    dump = retort.dump(my, MyType)
    assert dump == data


def test_retort_empty_message() -> None:
    retort = create_retort(warming_up=False)

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
    retort = create_retort(warming_up=False)

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
