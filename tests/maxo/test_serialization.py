import dataclasses
import typing

import pytest
from adaptix.load_error import LoadError

from maxo import methods, types
from maxo.bot.defaults import BotDefaults
from maxo.bot.methods import (
    AnswerOnCallback,
    EditMessage,
    GetMembers,
    GetMessages,
    GetUpdates,
    RemoveMember,
    SendMessage,
)
from maxo.bot.methods.base import MaxoMethod
from maxo.enums import ChatAdminPermission, TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_omitted
from maxo.serialization import (
    TypesWithFormat,
    TypesWithLinkPreview,
    create_retort,
    create_retort_with_bot,
)
from maxo.types import (
    BotAdminPermissionsChanged,
    CommentCreated,
    CommentEdited,
    CommentMessage,
    CommentRemoved,
    Message,
    MessageCreated,
    NewMessageBody,
    UpdateList,
    User,
)
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
    expected = "true" if default else "false"

    for method in (SendMessage(), AnswerOnCallback(callback_id="callback")):
        data = retort.dump(method)
        if is_omitted(default):
            assert "disable_link_preview" not in data["query"]
        else:
            assert data["query"]["disable_link_preview"] == expected


def test_bot_default_disable_link_preview_does_not_override_explicit() -> None:
    defaults = BotDefaults(disable_link_preview=True)
    retort = create_retort(defaults=defaults, warming_up=False)

    data = retort.dump(
        AnswerOnCallback(callback_id="callback", disable_link_preview=False),
    )
    assert data["query"]["disable_link_preview"] == "false"

    data = retort.dump(SendMessage(disable_link_preview=False))
    assert data["query"]["disable_link_preview"] == "false"


@pytest.mark.parametrize(("block", "expected"), [(True, "true"), (False, "false")])
def test_query_bool_is_dumped_as_json_literal(block: bool, expected: str) -> None:
    # Дампер квери-булей общий, поэтому проверяем и не-disable_link_preview поле.
    retort = create_retort(warming_up=False)

    data = retort.dump(RemoveMember(chat_id=1, user_id=2, block=block))

    assert data["query"]["block"] == expected


def test_retort_loads_user_without_last_activity_time() -> None:
    # MAX не присылает поле, если пользователь скрыл онлайн-статус.
    retort = create_retort(warming_up=False)

    user = retort.load(
        {"user_id": 1, "first_name": "Alice", "is_bot": False},
        User,
    )

    assert is_omitted(user.last_activity_time)
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_activity_time


def test_types_with_defaults_match_declared_fields() -> None:
    # Защита от расхождения: butcher может добавить поле в новый метод или
    # в новое тело запроса, а союзы в serialization.py руками не обновят.
    # Кандидатов собираем сканом, а не списком имён, иначе новый тип пройдёт
    # мимо проверки ровно так же, как мимо союза.
    candidates: set[type] = {
        obj
        for obj in (*vars(methods).values(), *vars(types).values())
        if isinstance(obj, type)
        and issubclass(obj, MaxoMethod | MaxoType)
        and dataclasses.is_dataclass(obj)
    }

    def owners(field_name: str) -> set[type]:
        return {
            candidate
            for candidate in candidates
            if any(field.name == field_name for field in dataclasses.fields(candidate))
        }

    assert owners("format") == set(typing.get_args(TypesWithFormat))
    assert owners("disable_link_preview") == set(
        typing.get_args(TypesWithLinkPreview),
    )


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


def test_retort_keeps_message_created_with_post_id_as_message() -> None:
    retort = create_retort(warming_up=False)
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
    retort = create_retort(warming_up=False)
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


def test_retort_loads_bot_admin_permissions_changed() -> None:
    retort = create_retort(warming_up=False)
    data = {
        "marker": 1,
        "updates": [
            {
                "update_type": "bot_admin_permissions_changed",
                "timestamp": 1234567890,
                "chat_id": 1,
                "user_id": 2,
                "bot_id": 3,
                "is_channel": True,
                "is_admin": True,
                "permissions": ["add_admins", "can_call"],
            },
        ],
    }

    update = retort.load(data, UpdateList).updates[0]

    assert isinstance(update, BotAdminPermissionsChanged)
    assert update.chat_id == 1
    assert update.user_id == 2
    assert update.bot_id == 3
    assert update.permissions == [
        ChatAdminPermission.ADD_ADMINS,
        ChatAdminPermission.CAN_CALL,
    ]
    assert retort.dump(update)["update_type"] == "bot_admin_permissions_changed"
