import pytest
from multidict import MultiDict

from maxo import Bot
from maxo.transport.webhook.route import BotIdParam, BotTokenParam, Const, Ref, Route
from maxo.transport.webhook.route.errors import (
    InvalidPathParamError,
    MissingQueryParamError,
    QueryParamMismatchError,
    UnexpectedQueryParamError,
)
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("base_path", "expected_path"),
    [
        ("", "/webhook"),
        ("/api", "/api/webhook"),
        ("/api/", "/api/webhook"),
    ],
    ids=["origin", "base-path", "base-path-trailing-slash"],
)
async def test_route_builds_static_webhook_url_under_base_path(
    bot: Bot,
    base_path: str,
    expected_path: str,
) -> None:
    route = Route(base_url=f"https://example.com{base_path}", path="/webhook")

    assert await route.build_url(bot=bot) == f"https://example.com{expected_path}"


@pytest.mark.asyncio
async def test_route_path_is_optional(bot: Bot) -> None:
    route = Route(base_url="https://example.com")

    assert route.path == "/"
    assert await route.build_url(bot=bot) == "https://example.com"


@pytest.mark.asyncio
async def test_route_builds_webhook_url_with_encoded_path_param(bot: Bot) -> None:
    base_url = "https://example.com:8080/api/v2/telegram"
    route = Route(
        base_url=base_url,
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
    )

    assert await route.build_url(bot=bot) == f"{base_url}/webhook/42%3ATEST"


@pytest.mark.asyncio
async def test_route_builds_webhook_url_with_query_params(bot: Bot) -> None:
    route = Route(
        base_url="https://example.com/api",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token"), "kind": ("telegram", "webhook")},
    )

    assert (
        await route.build_url(bot=bot)
        == "https://example.com/api/webhook/42%3ATEST?token=42:TEST&kind=telegram&kind=webhook"
    )


def test_route_normalizes_path_without_leading_slash() -> None:
    route = Route(
        base_url="https://example.com",
        path="webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
    )
    assert route.path == "/webhook/{bot_token}"


@pytest.mark.asyncio
async def test_route_parses_declared_path_params(bot_token: str) -> None:
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
    )

    request = DummyWebRequest(DummyRequest(path_params={"bot_token": bot_token}))

    assert await route.match(request) == {"bot_token": bot_token}


@pytest.mark.asyncio
async def test_route_reports_invalid_path_param_value() -> None:
    raw_bot_id = "not-int"
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_id}",
        params={"bot_id": BotIdParam()},
    )
    request = DummyWebRequest(DummyRequest(path_params={"bot_id": raw_bot_id}))

    with pytest.raises(InvalidPathParamError) as exc_info:
        await route.match(request)

    assert exc_info.value.param == "bot_id"
    assert exc_info.value.value == raw_bot_id


@pytest.mark.asyncio
async def test_route_matches_repeated_query_params_in_any_order(bot_token: str) -> None:
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token"), "kind": (Const("telegram"), "webhook")},
    )
    request = DummyWebRequest(
        DummyRequest(
            path_params={"bot_token": bot_token},
            query=MultiDict(
                [("token", bot_token), ("kind", "webhook"), ("kind", "telegram")],
            ),
        ),
    )

    assert await route.match(request) == {"bot_token": bot_token}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "available_query_params"),
    [
        (MultiDict(), ()),
        (MultiDict({"other": "value"}), ("other",)),
    ],
    ids=["no-query", "other-query"],
)
async def test_route_reports_missing_required_query_param(
    bot_token: str,
    query: MultiDict[str],
    available_query_params: tuple[str, ...],
) -> None:
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token")},
    )
    request = DummyWebRequest(
        DummyRequest(path_params={"bot_token": bot_token}, query=query),
    )

    with pytest.raises(MissingQueryParamError) as exc_info:
        await route.match(request)

    assert exc_info.value.query_param == "token"
    assert exc_info.value.available_query_params == available_query_params


@pytest.mark.asyncio
async def test_route_reports_query_param_value_mismatch(bot_token: str) -> None:
    wrong_token = "wrong"  # noqa: S105
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token")},
    )
    request = DummyWebRequest(
        DummyRequest(
            path_params={"bot_token": bot_token},
            query=MultiDict({"token": wrong_token}),
        ),
    )

    with pytest.raises(QueryParamMismatchError) as exc_info:
        await route.match(request)

    assert exc_info.value.query_param == "token"
    assert exc_info.value.expected == (bot_token,)
    assert exc_info.value.got == (wrong_token,)


@pytest.mark.asyncio
async def test_route_reports_unexpected_query_param(bot_token: str) -> None:
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token")},
        strict_query=True,
    )
    request = DummyWebRequest(
        DummyRequest(
            path_params={"bot_token": bot_token},
            query=MultiDict({"token": bot_token, "extra": "value"}),
        ),
    )

    with pytest.raises(UnexpectedQueryParamError) as exc_info:
        await route.match(request)

    assert exc_info.value.query_params == ("extra",)
    assert exc_info.value.expected_query_params == ("token",)


@pytest.mark.asyncio
async def test_route_allows_unexpected_query_param_by_default(bot_token: str) -> None:
    route = Route(
        base_url="https://example.com",
        path="/webhook/{bot_token}",
        params={"bot_token": BotTokenParam()},
        query={"token": Ref("bot_token")},
    )
    request = DummyWebRequest(
        DummyRequest(
            path_params={"bot_token": bot_token},
            query=MultiDict({"token": bot_token, "extra": "value"}),
        ),
    )

    assert await route.match(request) == {"bot_token": bot_token}


@pytest.mark.asyncio
async def test_route_reports_any_query_param_when_strict_query_has_no_query_spec() -> (
    None
):
    route = Route(base_url="https://example.com", path="/webhook", strict_query=True)
    request = DummyWebRequest(DummyRequest(query=MultiDict({"extra": "value"})))

    with pytest.raises(UnexpectedQueryParamError) as exc_info:
        await route.match(request)

    assert exc_info.value.query_params == ("extra",)
    assert exc_info.value.expected_query_params == ()
