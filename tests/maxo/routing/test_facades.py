"""Фасады - тонкие делегаты к полям апдейта, проверяем их скопом."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from maxo.enums import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.routing.facades import (
    BotAddedToChatFacade,
    BotRemovedFromChatFacade,
    BotStartedFacade,
    BotStoppedFacade,
    ChatTitleChangedFacade,
    DialogClearedFacade,
    DialogMutedFacade,
    DialogRemovedFacade,
    DialogUnmutedFacade,
    ErrorEventFacade,
    MessageCallbackFacade,
    MessageCreatedFacade,
    MessageEditedFacade,
    MessageRemovedFacade,
    UserAddedToChatFacade,
    UserRemovedFromChatFacade,
)
from maxo.routing.signals import MaxoUpdate
from maxo.types import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    Callback,
    ChatTitleChanged,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    ErrorEvent,
    Message,
    MessageBody,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    Recipient,
    User,
    UserAddedToChat,
    UserRemovedFromChat,
)
from tests.constants import NOW


def user() -> User:
    return User(user_id=1, is_bot=False, first_name="U", last_activity_time=NOW)


def message() -> Message:
    return Message(
        timestamp=NOW,
        recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
        body=MessageBody(mid="m", seq=1, text="t"),
    )


def callback_update(msg: Message | None = None) -> MessageCallback:
    return MessageCallback(
        timestamp=NOW,
        message=msg,
        callback=Callback(
            callback_id="cb",
            user=user(),
            timestamp=NOW,
            payload="p",
        ),
        user_locale="ru",
    )


CASES: list[tuple[Any, Any, tuple[str, ...]]] = [
    (
        BotAddedToChatFacade,
        BotAddedToChat(timestamp=NOW, chat_id=10, user=user(), is_channel=False),
        ("chat_id", "user", "is_channel"),
    ),
    (
        BotRemovedFromChatFacade,
        BotRemovedFromChat(timestamp=NOW, chat_id=10, user=user(), is_channel=True),
        ("chat_id", "user", "is_channel"),
    ),
    (
        BotStartedFacade,
        BotStarted(timestamp=NOW, chat_id=10, user=user(), payload="x"),
        ("chat_id", "user", "payload", "user_locale"),
    ),
    (
        BotStoppedFacade,
        BotStopped(timestamp=NOW, chat_id=10, user=user()),
        ("chat_id", "user", "user_locale"),
    ),
    (
        ChatTitleChangedFacade,
        ChatTitleChanged(timestamp=NOW, chat_id=10, user=user(), title="T"),
        ("chat_id", "user", "title"),
    ),
    (
        DialogClearedFacade,
        DialogCleared(timestamp=NOW, chat_id=10, user=user()),
        ("chat_id", "user", "user_locale"),
    ),
    (
        DialogMutedFacade,
        DialogMuted(timestamp=NOW, chat_id=10, user=user(), muted_until=NOW),
        ("chat_id", "user", "muted_until", "user_locale"),
    ),
    (
        DialogRemovedFacade,
        DialogRemoved(timestamp=NOW, chat_id=10, user=user()),
        ("chat_id", "user", "user_locale"),
    ),
    (
        DialogUnmutedFacade,
        DialogUnmuted(timestamp=NOW, chat_id=10, user=user()),
        ("chat_id", "user", "user_locale"),
    ),
    (
        MessageCreatedFacade,
        MessageCreated(timestamp=NOW, message=message()),
        ("message", "user_locale"),
    ),
    (
        MessageEditedFacade,
        MessageEdited(timestamp=NOW, message=message()),
        ("message",),
    ),
    (
        MessageRemovedFacade,
        MessageRemoved(timestamp=NOW, chat_id=10, message_id="m", user_id=1),
        ("chat_id", "message_id", "user_id"),
    ),
    (
        UserAddedToChatFacade,
        UserAddedToChat(timestamp=NOW, chat_id=10, user=user(), is_channel=False),
        ("chat_id", "user", "inviter_id", "is_channel"),
    ),
    (
        UserRemovedFromChatFacade,
        UserRemovedFromChat(timestamp=NOW, chat_id=10, user=user(), is_channel=False),
        ("chat_id", "user", "admin_id", "is_channel"),
    ),
    (
        MessageCallbackFacade,
        callback_update(message()),
        ("message", "callback", "user_locale", "callback_id", "payload", "user"),
    ),
]


@pytest.mark.parametrize(
    ("facade_cls", "update", "properties"),
    CASES,
    ids=lambda value: getattr(value, "__name__", ""),
)
def test_facade_delegates_properties(
    facade_cls: Any,
    update: Any,
    properties: tuple[str, ...],
) -> None:
    facade = facade_cls(bot=MagicMock(), update=update)

    for name in properties:
        assert getattr(facade, name) == getattr(update, name), name


def test_callback_facade_message_is_none_without_message() -> None:
    """MAX присылает `message=null`, если сообщение удалили до колбэка."""
    facade = MessageCallbackFacade(bot=MagicMock(), update=callback_update())

    assert facade.message is None

    with pytest.raises(AttributeIsEmptyError):
        _ = facade.unsafe_message


async def test_callback_facade_methods_raise_without_message() -> None:
    """Методы миксина ходят в сообщение через фасадную пропертю `message`."""
    facade = MessageCallbackFacade(bot=MagicMock(), update=callback_update())

    with pytest.raises(AttributeIsEmptyError):
        await facade.send_message("hi")


def test_callback_facade_unsafe_message_returns_message() -> None:
    update = callback_update(message())

    facade = MessageCallbackFacade(bot=MagicMock(), update=update)

    assert facade.unsafe_message is update.message


def test_base_facade_exposes_update() -> None:
    update = MessageCreated(timestamp=NOW, message=message())

    assert MessageCreatedFacade(bot=MagicMock(), update=update).update is update


def test_error_event_facade() -> None:
    inner = MessageCreated(timestamp=NOW, message=message())
    maxo_update = MaxoUpdate(update=inner)
    error = RuntimeError("boom")
    event: ErrorEvent[Any, Any] = ErrorEvent(exception=error, update=maxo_update)

    facade: ErrorEventFacade[Any, Any] = ErrorEventFacade(
        bot=MagicMock(),
        update=event,
    )

    assert facade.exception is error
    assert facade.error is error
    assert facade.update is maxo_update
    assert facade.event is inner
