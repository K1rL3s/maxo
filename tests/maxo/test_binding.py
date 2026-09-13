from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import AnswerOnCallback, EditMessage, GetMyInfo, SendMessage
from maxo.bot.warming_up import _LOADED_ROOTS, _METHOD_ROOTS
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
from maxo.types.binding import _field_classes
from tests.factories import make_bot

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


def test_warm_roots_cover_every_top_level_load() -> None:
    """
    Сверху грузятся возвращаемые типы методов - unihttp делает
    `response_loader.load(data, method.__returning__)`, - плюс `Updates`
    в вебхуке и `list[Attachments]` в сторадже диалогов.
    """
    returning = {method.__returning__ for method in _METHOD_ROOTS}
    assert returning <= set(_LOADED_ROOTS)
    assert Updates in _LOADED_ROOTS
    assert list[Attachments] in _LOADED_ROOTS


def test_defaults_land_in_dumped_request() -> None:
    defaults = BotDefaults(text_format=TextFormat.HTML, disable_link_preview=True)
    retort = get_retort()

    body = retort.dump(apply_defaults(SendMessage(chat_id=1, text="hi"), defaults))
    assert body["body"]["format"] == "html"
    assert body["query"]["disable_link_preview"] == 1

    edit = retort.dump(apply_defaults(EditMessage(message_id="m", text="hi"), defaults))
    assert edit["body"]["format"] == "html"


def test_bind_reaches_whole_tree_from_root() -> None:
    """`as_` и сеттер `bot` тоже идут по дереву, а не только по корню."""
    bot = make_bot()
    update = get_retort().load(UPDATE, Updates)

    update.as_(bot)
    assert update.message.bot is bot

    update.bot = None
    assert update.message._bot is None


def test_type_graph_is_acyclic() -> None:
    """
    _binds_bot рекурсивен и защиты от циклов не имеет.

    DFS + раскраска. Пример цикла: (A.b: B, B.a: A)
    """
    visiting: set[type] = set()
    visited: set[type] = set()

    def visit(current: type, path: list[str]) -> None:
        if current in visited:
            return
        assert current not in visiting, f"цикл в графе типов: {' -> '.join(path)}"

        visiting.add(current)
        for classes in _field_classes(current).values():
            for field_class in classes:
                visit(field_class, [*path, field_class.__name__])
        visiting.discard(current)
        visited.add(current)

    for root in _LOADED_ROOTS:
        visit(root, [getattr(root, "__name__", str(root))])
