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
    link = deeplink.create_start_link(bot=cast("Bot", bot), payload="test")
    assert link == "https://max.ru/testbot?start=test"


def test_create_startapp_link() -> None:
    bot = MockBot(username="testbot")
    link = deeplink.create_startapp_link(
        bot=cast("Bot", bot),
        payload="test",
        app_name="testapp",
    )
    assert link == "https://max.ru/testbot/testapp?startapp=test"


def test_create_startapp_link_long_payload() -> None:
    payload = "a" * deeplink.STARTAAPP_PAYLOAD_MAX_LEN
    link = deeplink.create_deep_link(
        username="testbot",
        link_type="startapp",
        payload=payload,
    )
    assert link == f"https://max.ru/testbot?startapp={payload}"


def test_create_startapp_link_payload_too_long() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "Payload must be up to "
            f"{deeplink.STARTAAPP_PAYLOAD_MAX_LEN} characters long."
        ),
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="startapp",
            payload="a" * (deeplink.STARTAAPP_PAYLOAD_MAX_LEN + 1),
        )


def test_create_start_link_keeps_short_limit() -> None:
    with pytest.raises(
        ValueError,
        match=f"Payload must be up to {deeplink.PAYLOAD_MAX_LEN} characters long.",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="start",
            payload="a" * (deeplink.PAYLOAD_MAX_LEN + 1),
        )


def test_create_startgroup_link_keeps_short_limit() -> None:
    with pytest.raises(
        ValueError,
        match=f"Payload must be up to {deeplink.PAYLOAD_MAX_LEN} characters long.",
    ):
        deeplink.create_deep_link(
            username="testbot",
            link_type="startgroup",
            payload="a" * (deeplink.PAYLOAD_MAX_LEN + 1),
        )
