import dataclasses
from typing import TYPE_CHECKING, Any

import pytest

from maxo import types
from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import AnswerOnCallback, EditMessage, GetMyInfo, SendMessage
from maxo.bot.warming_up import _LOADED_HINTS, _METHODS
from maxo.enums import TextFormat
from maxo.omit import is_defined, is_omitted
from maxo.serialization import get_retort
from maxo.types import (
    Attachments,
    ChatList,
    MessageCreated,
    NewMessageBody,
    Updates,
    bind_bot,
)
from maxo.types.base import FacadeMaxoType, MaxoType
from maxo.types.facades.bot import BotMethodsFacade
from tests.factories import make_bot

if TYPE_CHECKING:
    from maxo.types import Message

UPDATE = {
    "update_type": "message_created",
    "timestamp": 1700000000000,
    "message": {
        "timestamp": 1700000000000,
        "sender": {
            "user_id": 1,
            "first_name": "a",
            "is_bot": False,
            "last_activity_time": 1700000000000,
        },
        "recipient": {"chat_type": "dialog"},
        "body": {"mid": "m", "seq": 1, "text": "hi"},
    },
}
CHAT = {
    "chat_id": 1,
    "type": "chat",
    "status": "active",
    "last_event_time": 1700000000000,
    "participants_count": 2,
    "is_public": False,
    "pinned_message": UPDATE["message"],
}


def test_defaults_fill_omitted() -> None:
    defaults = BotDefaults(text_format=TextFormat.MARKDOWN)
    method = apply_defaults(SendMessage(chat_id=1, text="hi"), defaults)
    assert method.format == TextFormat.MARKDOWN


def test_defaults_do_not_override_explicit() -> None:
    defaults = BotDefaults(text_format=TextFormat.MARKDOWN)
    method = apply_defaults(
        SendMessage(chat_id=1, text="hi", format=TextFormat.HTML),
        defaults,
    )
    assert method.format == TextFormat.HTML


def test_defaults_do_not_mutate_source() -> None:
    """Объект метода принадлежит вызывающему - его могут отправить двумя ботами."""
    method = SendMessage(chat_id=1, text="hi")
    apply_defaults(method, BotDefaults(text_format=TextFormat.MARKDOWN))
    assert is_omitted(method.format)


def test_defaults_reach_nested_new_message_body() -> None:
    """Единственное вложенное место во всём дереве методов."""
    defaults = BotDefaults(text_format=TextFormat.HTML)
    method = apply_defaults(
        AnswerOnCallback(callback_id="c", message=NewMessageBody(text="x")),
        defaults,
    )
    assert is_defined(method.message)
    assert method.message.format == TextFormat.HTML


def test_defaults_ignore_other_methods() -> None:
    method = GetMyInfo()
    assert apply_defaults(method, BotDefaults()) is method


def test_bind_root_and_nested() -> None:
    bot = make_bot()
    update = bind_bot(get_retort().load(UPDATE, Updates), bot)

    assert isinstance(update, MessageCreated)
    assert update.bot is bot
    assert update.message.bot is bot


def test_bind_walks_lists() -> None:
    bot = make_bot()
    chats = bind_bot(
        get_retort().load({"chats": [dict(CHAT)] * 3, "marker": None}, ChatList),
        bot,
    )

    assert len(chats.chats) == 3
    assert all(is_defined(chat.pinned_message) for chat in chats.chats)
    assert all(chat.pinned_message.bot is bot for chat in chats.chats)  # type: ignore[union-attr]


def test_bind_ignores_non_maxo_values() -> None:
    bot = make_bot()
    assert bind_bot(b"raw", bot) == b"raw"
    assert bind_bot(None, bot) is None


def test_warm_hints_cover_every_top_level_load() -> None:
    """
    Сверху грузятся возвращаемые типы методов - unihttp делает
    `response_loader.load(data, method.__returning__)`, - плюс `Updates`
    в вебхуке и `list[Attachments]` в сторадже диалогов.
    """
    returning = {method.__returning__ for method in _METHODS}
    assert returning <= set(_LOADED_HINTS)
    assert Updates in _LOADED_HINTS
    assert list[Attachments] in _LOADED_HINTS


def test_defaults_land_in_dumped_request() -> None:
    defaults = BotDefaults(text_format=TextFormat.HTML, disable_link_preview=True)
    retort = get_retort()

    body = retort.dump(apply_defaults(SendMessage(chat_id=1, text="hi"), defaults))
    assert body["body"]["format"] == "html"
    assert body["query"]["disable_link_preview"] == "true"

    edit = retort.dump(apply_defaults(EditMessage(message_id="m", text="hi"), defaults))
    assert edit["body"]["format"] == "html"


def test_bind_reaches_whole_tree_from_root() -> None:
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates)

    update.as_(bot)
    assert update.message.bot is bot

    update.as_(None)
    assert update.message._bot is None


def test_bind_descends_into_dict_values() -> None:
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates)

    bind_bot({"key": update}, bot)

    assert update.message.bot is bot


def test_bind_handles_cycles_in_containers() -> None:
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates)
    values: list[Any] = []
    values.append(values)
    values.append({"update": update})

    bind_bot(values, bot)

    assert update.message.bot is bot


class _Node(FacadeMaxoType):
    peer: "_Node | None" = None


def test_bind_handles_cycles_in_dataclasses() -> None:
    bot = make_bot()
    first = _Node()
    second = _Node(peer=first)
    first.peer = second

    bind_bot(first, bot)

    assert first.bot is bot
    assert second.bot is bot


def test_replace_keeps_bot() -> None:
    # The bot is a field, so `dataclasses.replace` keeps it.
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates).as_(bot)

    copied = dataclasses.replace(update, user_locale="ru")

    assert copied.bot is bot
    assert copied.message.bot is bot


def test_retort_does_not_read_or_write_bot() -> None:
    retort = get_retort()

    update = retort.load({**UPDATE, "_bot": "evil"}, Updates)
    assert update._bot is None

    assert "_bot" not in retort.dump(update.as_(make_bot()), Updates)


def test_facade_types_hold_bot() -> None:
    # A facade without `FacadeMaxoType` would fail on `self.bot` only at runtime.
    facade_types = [
        obj
        for obj in vars(types).values()
        if isinstance(obj, type) and issubclass(obj, BotMethodsFacade)
    ]

    assert facade_types
    assert [t for t in facade_types if not issubclass(t, FacadeMaxoType)] == []


class _TypeCheckingOnly(MaxoType):
    # `Message` is imported only under `TYPE_CHECKING`.
    messages: "list[Message]" = dataclasses.field(default_factory=list)


def test_bind_follows_type_checking_only_hints() -> None:
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates)
    assert isinstance(update, MessageCreated)

    bind_bot(_TypeCheckingOnly(messages=[update.message]), bot)

    assert update.message.bot is bot


class _CycleLeaf(FacadeMaxoType):
    pass


class _CycleA(MaxoType):
    b: "_CycleB | None" = None
    leaf: _CycleLeaf | None = None


class _CycleB(MaxoType):
    a: _CycleA | None = None


class _LoopA(MaxoType):
    b: "_LoopB | None" = None


class _LoopB(MaxoType):
    a: _LoopA | None = None


def test_bind_handles_cycles_in_types() -> None:
    # `_CycleB` leads to the facade only through `_CycleA`, which leads back.
    bot = make_bot()
    leaf = _CycleLeaf()

    bind_bot(_CycleB(a=_CycleA(leaf=leaf)), bot)
    bind_bot(_LoopB(a=_LoopA()), bot)  # no facade: the walk must still end

    assert leaf.bot is bot


class _Unresolvable(MaxoType):
    # The name exists nowhere: a bug in the hint, not something to walk around.
    value: "_Missing | None" = None  # type: ignore[name-defined]  # noqa: F821


def test_bind_raises_on_unresolvable_hint() -> None:
    with pytest.raises(NameError, match="_Missing"):
        bind_bot(_Unresolvable(), make_bot())
