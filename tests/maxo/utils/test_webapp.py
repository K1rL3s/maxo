import hashlib
import hmac
import json
from typing import Any
from urllib.parse import urlencode

import pytest

from maxo.errors import InvalidWebAppInitDataError
from maxo.utils.webapp import (
    WebAppChat,
    WebAppInitData,
    WebAppUser,
    check_webapp_signature,
    parse_webapp_init_data,
    safe_parse_webapp_init_data,
)
from tests.constants import TOKEN

TEST_DATA = {
    "query_id": "test_query_id",
    "user": json.dumps(
        {
            "id": 1,
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
            "language_code": "en",
            "photo_url": "https://example.com/photo.jpg",
        },
    ),
    "chat": json.dumps({"id": 1, "type": "private"}),
    "auth_date": "123456789",
    "start_param": "test",
}


def generate_test_init_data(token: str, data: dict[str, Any]) -> str:
    sorted_data = dict(sorted(data.items()))
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_data.items())

    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)

    sorted_data["hash"] = h.hexdigest()

    return urlencode(sorted_data)


@pytest.fixture
def valid_init_data() -> str:
    return generate_test_init_data(TOKEN, TEST_DATA)


def test_check_webapp_signature_valid(valid_init_data: str) -> None:
    assert check_webapp_signature(TOKEN, valid_init_data) is True


def test_check_webapp_signature_invalid() -> None:
    assert check_webapp_signature(TOKEN, "hash=invalid&...some_other_data") is False
    assert check_webapp_signature(TOKEN, "some_other_data") is False


def test_parse_webapp_init_data(valid_init_data: str) -> None:
    parsed_data = parse_webapp_init_data(valid_init_data)
    assert isinstance(parsed_data, WebAppInitData)
    assert parsed_data.query_id == "test_query_id"
    assert parsed_data.start_param == "test"

    assert isinstance(parsed_data.user, WebAppUser)
    assert parsed_data.user.id == 1
    assert parsed_data.user.first_name == "Test"
    assert parsed_data.user.last_name == "User"
    assert parsed_data.user.username == "testuser"
    assert parsed_data.user.language_code == "en"
    assert parsed_data.user.photo_url == "https://example.com/photo.jpg"

    assert isinstance(parsed_data.chat, WebAppChat)
    assert parsed_data.chat.id == 1
    assert parsed_data.chat.type == "private"


def test_safe_parse_webapp_init_data_valid(valid_init_data: str) -> None:
    parsed_data = safe_parse_webapp_init_data(TOKEN, valid_init_data)
    assert isinstance(parsed_data, WebAppInitData)


def test_safe_parse_webapp_init_data_invalid() -> None:
    with pytest.raises(
        InvalidWebAppInitDataError,
        match="Invalid init data signature",
    ) as exc_info:
        safe_parse_webapp_init_data(TOKEN, "hash=invalid&...some_other_data")
    assert isinstance(exc_info.value, ValueError)


def test_parse_webapp_init_data_ignores_unknown_fields() -> None:
    init_data = urlencode(
        {
            "hash": "x",
            "some_new_field": "1",
            "user": json.dumps({"id": 1, "first_name": "Test", "is_premium": True}),
            "chat": json.dumps({"id": 2, "type": "DIALOG", "title": "Chat"}),
        },
    )

    parsed_data = parse_webapp_init_data(init_data)

    assert parsed_data.hash == "x"
    assert parsed_data.user.id == 1
    assert parsed_data.chat.id == 2


@pytest.mark.parametrize(
    "data",
    [
        {"hash": "x"},
        {"hash": "x", "chat": TEST_DATA["chat"]},
        {"chat": TEST_DATA["chat"], "user": TEST_DATA["user"]},
        {"hash": "x", "chat": '{"id": 1}', "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "{broken}", "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "private", "user": TEST_DATA["user"]},
    ],
)
def test_parse_webapp_init_data_malformed(data: dict[str, str]) -> None:
    with pytest.raises(InvalidWebAppInitDataError):
        parse_webapp_init_data(urlencode(data))
