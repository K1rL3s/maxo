from typing import cast

import pytest

from maxo import Bot
from maxo.utils import deeplink
from tests.mocks import MockBot


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
        match="Payload must be up to 128 characters long",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="start",
            payload="a" * 129,
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
    link = deeplink.create_start_link(bot=cast("Bot", bot), payload="test")
    assert link == "https://max.ru/testbot?start=test"


def test_create_startapp_link() -> None:
    bot = MockBot(username="testbot")
    link = deeplink.create_startapp_link(
        bot=cast("Bot", bot),
        payload="test",
    )
    assert link == "https://max.ru/testbot?startapp=test"


def test_create_startapp_link_long_payload() -> None:
    payload = "a" * 512
    link = deeplink.create_deep_link(
        username="testbot",
        link_type="startapp",
        payload=payload,
    )
    assert link == f"https://max.ru/testbot?startapp={payload}"


def test_create_startapp_link_payload_too_long() -> None:
    with pytest.raises(
        ValueError,
        match="Payload must be up to 512 characters long",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="startapp",
            payload="a" * 513,
        )


def test_create_start_link_keeps_short_limit() -> None:
    with pytest.raises(
        ValueError,
        match="Payload must be up to 128 characters long",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="start",
            payload="a" * 129,
        )
