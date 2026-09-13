import hashlib
import hmac
import json
from typing import Any
from unittest.mock import Mock
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


@pytest.mark.parametrize(
    "init_data",
    ["hash=invalid&...some_other_data", "hash=%D1%84", "hash=x&a=\ud800"],
)
def test_safe_parse_webapp_init_data_invalid(init_data: str) -> None:
    with pytest.raises(
        InvalidWebAppInitDataError,
        match="Invalid init data signature",
    ) as exc_info:
        safe_parse_webapp_init_data(TOKEN, init_data)
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
        {"hash": "x", "chat": TEST_DATA["chat"]},
        {"chat": TEST_DATA["chat"], "user": TEST_DATA["user"]},
        {"hash": "x", "chat": '{"id": 1}', "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "{broken}", "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "[1, 2]", "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "null", "user": TEST_DATA["user"]},
        {"hash": "x", "chat": "[" * 10000 + "]" * 10000, "user": TEST_DATA["user"]},
    ],
)
def test_parse_webapp_init_data_malformed(data: dict[str, str]) -> None:
    with pytest.raises(InvalidWebAppInitDataError):
        parse_webapp_init_data(urlencode(data))


class LoaderError(Exception):
    pass


def test_parse_webapp_init_data_wraps_loader_error(valid_init_data: str) -> None:
    error = LoaderError()

    with pytest.raises(InvalidWebAppInitDataError) as exc_info:
        parse_webapp_init_data(valid_init_data, loads=Mock(side_effect=error))

    assert exc_info.value.__cause__ is error


@pytest.mark.parametrize("start_param", ["[1,2]", "{abc}"])
def test_parse_webapp_init_data_keeps_other_fields_as_strings(start_param: str) -> None:
    init_data = urlencode({**TEST_DATA, "hash": "x", "start_param": start_param})

    assert parse_webapp_init_data(init_data).start_param == start_param


DOCS_INIT_DATA = "chat=%7B%22id%22%3A12345%2C%22type%22%3A%22DIALOG%22%7D&ip=192.168.0.1&user=%7B%22id%22%3A67890%2C%22first_name%22%3A%22Max%22%2C%22last_name%22%3A%22User%22%2C%22username%22%3Anull%2C%22language_code%22%3A%22ru%22%2C%22photo_url%22%3Anull%7D&query_id=4c0ab423-342b-4e45-aea4-2747dbc500cd&auth_date=1771409719&hash=<calculated_hash>"
DOCS_LAUNCH_PARAMS = 'auth_date=1771409719\nchat={"id":12345,"type":"DIALOG"}\nip=192.168.0.1\nquery_id=4c0ab423-342b-4e45-aea4-2747dbc500cd\nuser={"id":67890,"first_name":"Max","last_name":"User","username":null,"language_code":"ru","photo_url":null}'


def test_safe_parse_webapp_init_data_docs_example() -> None:
    secret_key = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    hash_ = hmac.new(secret_key, DOCS_LAUNCH_PARAMS.encode(), hashlib.sha256)
    init_data = DOCS_INIT_DATA.replace("<calculated_hash>", hash_.hexdigest())

    assert safe_parse_webapp_init_data(TOKEN, init_data) == WebAppInitData(
        ip="192.168.0.1",
        query_id="4c0ab423-342b-4e45-aea4-2747dbc500cd",
        chat=WebAppChat(id=12345, type="DIALOG"),
        user=WebAppUser(
            id=67890,
            first_name="Max",
            last_name="User",
            language_code="ru",
        ),
        auth_date="1771409719",
        hash=hash_.hexdigest(),
    )
