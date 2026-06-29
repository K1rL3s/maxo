from datetime import UTC, datetime

import pytest

from maxo import Bot
from maxo.utils import deeplink


class MockBotInfo(Bot):
    def __init__(self, user_id: int, username: str) -> None:
        self.user_id = user_id
        self.username = username
        self.first_name = "Test"
        self.is_bot = True
        self.last_activity_time = datetime.fromtimestamp(1234567890, tz=UTC)


class MockBotState:
    def __init__(self, user_id: int, username: str) -> None:
        self.info = MockBotInfo(user_id, username)


class MockBot:
    def __init__(self, user_id: int = 1, username: str = "testbot") -> None:
        self.state = MockBotState(user_id, username)


def test_create_deep_link() -> None:
    link = deeplink.create_deep_link(
        username="testbot",
        link_type="start",
        payload="test",
    )
    assert link == "https://max.ru/testbot?start=test"


def test_create_deep_link_invalid_payload() -> None:
    with pytest.raises(ValueError, match="Wrong payload!"):
        deeplink.create_deep_link(
            username="testbot",
            link_type="start",
            payload="test payload",
        )


def test_create_deep_link_long_payload() -> None:
    with pytest.raises(
        ValueError,
        match=f"Payload must be up to {deeplink.PAYLOAD_MAX_LEN} characters long.",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="start",
            payload="a" * (deeplink.PAYLOAD_MAX_LEN + 1),
        )


def test_create_deep_link_encoded() -> None:
    link = deeplink.create_deep_link(
        username="testbot",
        link_type="start",
        payload="test payload",
        encode=True,
    )
    assert link == "https://max.ru/testbot?start=dGVzdCBwYXlsb2Fk"


def test_create_start_link() -> None:
    bot = MockBot(username="testbot")
    link = deeplink.create_start_link(bot=bot, payload="test")
    assert link == "https://max.ru/testbot?start=test"


def test_create_startapp_link() -> None:
    bot = MockBot(username="testbot")
    link = deeplink.create_startapp_link(bot=bot, payload="test", app_name="testapp")
    assert link == "https://max.ru/testbot/testapp?startapp=test"
