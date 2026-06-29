from datetime import UTC, datetime

import pytest

from maxo.enums import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omitted
from maxo.routing.updates.bot_started import BotStarted
from maxo.types.user import User


def create_user(user_id: int) -> User:
    return User(
        user_id=user_id,
        first_name=f"Test{user_id}",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )


def test_bot_started_constructor() -> None:
    user = create_user(1)
    bot_started = BotStarted(
        chat_id=123,
        user=user,
        payload="start_payload",
        user_locale="ru-RU",
        timestamp=datetime.now(UTC),
    )
    assert bot_started.chat_id == 123
    assert bot_started.user is user
    assert bot_started.payload == "start_payload"
    assert bot_started.user_locale == "ru-RU"
    assert bot_started.type == UpdateType.BOT_STARTED


def test_bot_started_unsafe_payload_defined() -> None:
    user = create_user(1)
    bot_started = BotStarted(
        chat_id=123,
        user=user,
        payload="start_payload",
        timestamp=datetime.now(UTC),
    )
    assert bot_started.unsafe_payload == "start_payload"


def test_bot_started_unsafe_payload_omitted() -> None:
    user = create_user(1)
    bot_started = BotStarted(
        chat_id=123,
        user=user,
        payload=Omitted(),
        timestamp=datetime.now(UTC),
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = bot_started.unsafe_payload


def test_bot_started_unsafe_user_locale_defined() -> None:
    user = create_user(1)
    bot_started = BotStarted(
        chat_id=123,
        user=user,
        user_locale="ru-RU",
        timestamp=datetime.now(UTC),
    )
    assert bot_started.unsafe_user_locale == "ru-RU"


def test_bot_started_unsafe_user_locale_omitted() -> None:
    user = create_user(1)
    bot_started = BotStarted(
        chat_id=123,
        user=user,
        user_locale=Omitted(),
        timestamp=datetime.now(UTC),
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = bot_started.unsafe_user_locale
