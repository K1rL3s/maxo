from typing import Any

import pytest
from yarl import URL

from maxo import Bot
from maxo.transport.webhook.routing import PathRouting, QueryRouting, StaticRouting

from .fixtures import DummyBoundRequest, DummyRequest


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/webhook",
        "https://example.com/webhook/",
        "https://example.com/webhook/any/path",
        "https://example.com/webhook?foo=bar",
    ],
)
def test_static_routing(url: str, bot: Bot) -> None:
    routing = StaticRouting(url=url)
    assert routing.webhook_point(bot) == url


@pytest.mark.parametrize(
    ("url", "param", "token", "path_params", "expected_url", "expected_token"),
    [
        (
            "https://example.com/webhook/{token}",
            "token",
            "42:TEST",
            {"token": "42:TEST"},
            "https://example.com/webhook/42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook/{token}",
            "token",
            "42:TEST",
            {},
            "https://example.com/webhook/42:TEST",
            None,
        ),
        (
            "https://example.com/webhook/{mytoken}",
            "mytoken",
            "42:TEST",
            {"mytoken": "42:TEST"},
            "https://example.com/webhook/42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook/{mytoken}",
            "mytoken",
            "42:TEST",
            {},
            "https://example.com/webhook/42:TEST",
            None,
        ),
    ],
    ids=[
        "standard-param-present",
        "standard-param-missing",
        "custom-param-present",
        "custom-param-missing",
    ],
)
def test_path_routing(
    url: str,
    param: str,
    token: str,
    path_params: dict[str, str] | dict[Any, Any],
    expected_url: str,
    expected_token: str | None,
) -> None:
    routing = PathRouting(url=url, param=param)
    assert routing.webhook_point(Bot(token)) == expected_url
    req = DummyBoundRequest(DummyRequest(path_params=path_params))
    assert routing.extract_token(req) == expected_token


@pytest.mark.parametrize(
    ("url", "param", "token", "query_params", "expected_url", "expected_token"),
    [
        (
            "https://example.com/webhook",
            "token",
            "42:TEST",
            {"token": "42:TEST"},
            "https://example.com/webhook?token=42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook",
            "token",
            "42:TEST",
            {},
            "https://example.com/webhook?token=42:TEST",
            None,
        ),
        (
            "https://example.com/webhook",
            "mytoken",
            "42:TEST",
            {"mytoken": "42:TEST"},
            "https://example.com/webhook?mytoken=42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook",
            "mytoken",
            "42:TEST",
            {},
            "https://example.com/webhook?mytoken=42:TEST",
            None,
        ),
        (
            "https://example.com/webhook?other=value",
            "token",
            "42:TEST",
            {"token": "42:TEST", "other": "value"},
            "https://example.com/webhook?other=value&token=42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook?foo=bar&baz=qux",
            "token",
            "42:TEST",
            {"token": "42:TEST", "foo": "bar", "baz": "qux"},
            "https://example.com/webhook?foo=bar&baz=qux&token=42:TEST",
            "42:TEST",
        ),
        (
            "https://example.com/webhook?token=old_value&other=value",
            "token",
            "42:TEST",
            {"token": "42:TEST", "other": "value"},
            "https://example.com/webhook?token=42:TEST&other=value",
            "42:TEST",
        ),
        (
            "https://example.com/webhook?api_key=secret&debug=true",
            "bot_token",
            "123:ABC",
            {"bot_token": "123:ABC", "api_key": "secret", "debug": "true"},
            "https://example.com/webhook?api_key=secret&debug=true&bot_token=123:ABC",
            "123:ABC",
        ),
    ],
    ids=[
        "standard-param-present",
        "standard-param-missing",
        "custom-param-present",
        "custom-param-missing",
        "preserve-existing-params",
        "preserve-multiple-params",
        "override-token-param",
        "complex-params",
    ],
)
def test_query_routing(
    url: str,
    param: str,
    token: str,
    query_params: dict[str, str] | dict[Any, Any],
    expected_url: str,
    expected_token: str | None,
) -> None:
    routing = QueryRouting(url=url, param=param)
    webhook_url = routing.webhook_point(Bot(token))

    # Parse both URLs to compare query params (order may differ)
    expected = URL(expected_url)
    actual = URL(webhook_url)

    # Check that all expected query params are present
    assert dict(actual.query) == dict(
        expected.query,
    ), f"Query parameters mismatch. Expected: {dict(expected.query)}, Got: {dict(actual.query)}"

    # Check token extraction
    req = DummyBoundRequest(DummyRequest(query_params=query_params))
    assert routing.extract_token(req) == expected_token
