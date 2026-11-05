import logging
from json import JSONDecodeError
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from adaptix.load_error import LoadError
from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from fastapi import FastAPI
from fastapi.testclient import TestClient

from maxo import Bot, Dispatcher, loggers
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.adapters.aiohttp.adapter import AiohttpWebAdapter
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.adapters.fastapi.adapter import FastApiWebAdapter
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security
from maxo.transport.webhook.security.secret_token import (
    SECRET_HEADER,
    StaticSecretToken,
)
from maxo.types import Updates

from .fixtures import DummyAdapter, DummyBoundRequest, DummyRequest


class JsonBoundRequest(DummyBoundRequest):
    def __init__(
        self,
        payload: dict[str, Any] | None = None,
        request: DummyRequest | None = None,
    ) -> None:
        super().__init__(request)
        self.payload = payload or {}

    async def json(self) -> dict[str, Any]:
        return self.payload


class JsonErrorBoundRequest(DummyBoundRequest):
    async def json(self) -> dict[str, Any]:
        raise JSONDecodeError("bad json", "", 0)


class DummyEngine(WebhookEngine):
    def __init__(
        self,
        dispatcher: Dispatcher,
        /,
        web_adapter: WebAdapter,
        bot: Bot | None = None,
        security: Security | None = None,
        handle_in_background: bool = False,
    ) -> None:
        super().__init__(
            dispatcher,
            web_adapter=web_adapter,
            routing=StaticRouting("https://example.com/webhook"),
            security=security,
            handle_in_background=handle_in_background,
        )
        self.bot = bot

    def _get_bot_from_request(self, bound_request: BoundRequest[Any]) -> Bot | None:
        return self.bot

    async def set_webhook(self, *args: Any, **kwargs: Any) -> Bot:
        if self.bot is None:
            raise RuntimeError("Bot is not configured")
        return self.bot

    async def on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        return None

    async def on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        return None


def make_bot(update: Updates | None = None, load_error: bool = False) -> MagicMock:
    bot = MagicMock(spec=Bot)
    bot.retort = MagicMock()
    if load_error:
        bot.retort.load.side_effect = LoadError
    else:
        bot.retort.load.return_value = update or MagicMock(spec=Updates)
    bot.silent_call_method = AsyncMock()
    return bot


async def test_handle_request_returns_400_when_bot_not_found() -> None:
    engine = DummyEngine(Dispatcher(), web_adapter=DummyAdapter())

    assert await engine.handle_request(DummyBoundRequest()) == (
        400,
        {"detail": "Bot not found"},
    )


async def test_handle_request_returns_403_when_security_fails() -> None:
    security = MagicMock(spec=Security)
    security.verify = AsyncMock(return_value=False)
    bot = make_bot()
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=bot, security=security)

    assert await engine.handle_request(DummyBoundRequest()) == (
        403,
        {"detail": "Forbidden"},
    )
    security.verify.assert_awaited_once()


async def test_handle_request_returns_400_for_invalid_json() -> None:
    bot = make_bot()
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=bot)

    assert await engine.handle_request(JsonErrorBoundRequest()) == (
        400,
        {"detail": "Bad request"},
    )


async def test_handle_request_returns_200_for_load_error() -> None:
    bot = make_bot(load_error=True)
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=bot)

    assert await engine.handle_request(JsonBoundRequest({"bad": "payload"})) == (
        200,
        {},
    )
    bot.retort.load.assert_called_once_with({"bad": "payload"}, Updates)


async def test_handle_request_dispatches_update() -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    update = MagicMock(spec=Updates)
    bot = make_bot(update)
    engine = DummyEngine(dispatcher, DummyAdapter(), bot=bot)

    assert await engine.handle_request(JsonBoundRequest({"update": "payload"})) == (
        200,
        {},
    )

    dispatcher.feed_max_update.assert_awaited_once()
    await_args = dispatcher.feed_max_update.await_args
    assert await_args is not None
    call_kwargs = await_args.kwargs
    assert call_kwargs["bot"] is bot
    assert isinstance(call_kwargs["update"], MaxoUpdate)
    assert call_kwargs["update"].update is update


async def test_handle_request_background_tracks_task() -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    bot = make_bot()
    engine = DummyEngine(
        dispatcher,
        DummyAdapter(),
        bot=bot,
        handle_in_background=True,
    )

    assert await engine.handle_request(JsonBoundRequest({"update": "payload"})) == (
        200,
        {},
    )
    await engine._task_tracker.close(timeout=1)

    dispatcher.feed_max_update.assert_awaited_once()


def test_register_delegates_to_adapter() -> None:
    dispatcher = Dispatcher()
    adapter = MagicMock(spec=WebAdapter)
    engine = DummyEngine(dispatcher, adapter, bot=make_bot())
    app = object()

    engine.register(app)

    adapter.register.assert_called_once_with(
        app=app,
        path="/webhook",
        handler=engine.handle_request,
        on_startup=engine.on_startup,
        on_shutdown=engine.on_shutdown,
    )


def test_build_workflow_data_merges_dispatcher_data_and_kwargs() -> None:
    dispatcher = Dispatcher(workflow_data={"foo": "bar"})
    engine = DummyEngine(dispatcher, DummyAdapter(), bot=make_bot())
    app = object()

    workflow_data = engine._build_workflow_data(app, foo="override", extra="value")

    assert workflow_data["app"] is app
    assert workflow_data["webhook_engine"] is engine
    assert workflow_data["dispatcher"] is dispatcher
    assert workflow_data["router"] is dispatcher
    assert workflow_data["dp"] is dispatcher
    assert workflow_data["foo"] == "override"
    assert workflow_data["extra"] == "value"


def test_register_warns_without_security(caplog: pytest.LogCaptureFixture) -> None:
    engine = DummyEngine(Dispatcher(), MagicMock(spec=WebAdapter), bot=make_bot())

    with caplog.at_level(logging.INFO, logger=loggers.webhook.name):
        engine.register(object())

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "/webhook" in warnings[0].getMessage()
    assert any(r.levelno == logging.INFO for r in caplog.records)


def test_register_does_not_warn_with_security(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(
        Dispatcher(),
        MagicMock(spec=WebAdapter),
        bot=make_bot(),
        security=MagicMock(spec=Security),
    )

    with caplog.at_level(logging.INFO, logger=loggers.webhook.name):
        engine.register(object())

    assert [(r.name, r.levelno) for r in caplog.records] == [
        (loggers.webhook.name, logging.INFO),
    ]


async def test_handle_request_logs_forbidden_without_secret(
    caplog: pytest.LogCaptureFixture,
) -> None:
    expected = "expected-secret-value"
    received = "received-secret-value"
    engine = DummyEngine(
        Dispatcher(),
        DummyAdapter(),
        bot=make_bot(),
        security=Security(secret_token=StaticSecretToken(expected)),
    )
    request = DummyBoundRequest(DummyRequest(headers={SECRET_HEADER: received}))

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        response = await engine.handle_request(request)

    assert response == (403, {"detail": "Forbidden"})
    assert [(r.name, r.levelno) for r in caplog.records] == [
        (loggers.webhook.name, logging.WARNING),
    ]
    assert "/webhook" in caplog.text
    assert expected not in caplog.text
    assert received not in caplog.text


async def test_handle_request_logs_bot_not_found(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(Dispatcher(), DummyAdapter())

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        await engine.handle_request(DummyBoundRequest())

    assert [r.levelno for r in caplog.records] == [logging.WARNING]


async def test_handle_request_logs_invalid_json(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=make_bot())

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        await engine.handle_request(JsonErrorBoundRequest())

    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert caplog.records[0].exc_info is None


async def test_handle_request_logs_load_error_with_traceback(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(
        Dispatcher(),
        DummyAdapter(),
        bot=make_bot(load_error=True),
    )

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        await engine.handle_request(JsonBoundRequest({"bad": "payload"}))

    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert caplog.records[0].exc_info is not None


async def test_handle_request_logs_accepted_update_at_debug(
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    engine = DummyEngine(dispatcher, DummyAdapter(), bot=make_bot())

    with caplog.at_level(logging.DEBUG, logger=loggers.webhook.name):
        await engine.handle_request(JsonBoundRequest({"update": "payload"}))

    assert [r.levelno for r in caplog.records] == [logging.DEBUG]


UNKNOWN_UPDATE_TYPE: dict[str, Any] = {
    "update_type": "some_new_event",
    "timestamp": 1700000000000,
}
UNKNOWN_ATTACHMENT_TYPE: dict[str, Any] = {
    "update_type": "message_created",
    "timestamp": 1700000000000,
    "message": {
        "sender": {
            "user_id": 1,
            "first_name": "a",
            "is_bot": False,
            "last_activity_time": 1700000000000,
        },
        "recipient": {"chat_type": "dialog", "chat_id": 1, "user_id": 2},
        "timestamp": 1700000000000,
        "body": {
            "mid": "m",
            "seq": 1,
            "text": "hi",
            "attachments": [{"type": "hologram", "payload": {}}],
        },
    },
}


@pytest.mark.parametrize("handle_in_background", [True, False])
@pytest.mark.parametrize(
    "raw_update",
    [UNKNOWN_UPDATE_TYPE, UNKNOWN_ATTACHMENT_TYPE],
    ids=["unknown_update_type", "unknown_attachment_type"],
)
async def test_handle_request_skips_unloadable_update(
    raw_update: dict[str, Any],
    handle_in_background: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    engine = DummyEngine(
        dispatcher,
        DummyAdapter(),
        bot=Bot("token"),
        handle_in_background=handle_in_background,
    )

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        response = await engine.handle_request(JsonBoundRequest(raw_update))
    await engine._task_tracker.close(timeout=1)

    assert response == (200, {})
    dispatcher.feed_max_update.assert_not_awaited()
    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert caplog.records[0].exc_info is not None
    assert str(raw_update) in caplog.text


async def test_handle_request_still_dispatches_loadable_update() -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    engine = DummyEngine(
        dispatcher,
        DummyAdapter(),
        bot=Bot("token"),
        handle_in_background=False,
    )
    raw_update = {
        **UNKNOWN_ATTACHMENT_TYPE,
        "message": {
            **UNKNOWN_ATTACHMENT_TYPE["message"],
            "body": {"mid": "m", "seq": 1, "text": "hi", "attachments": []},
        },
    }

    assert await engine.handle_request(JsonBoundRequest(raw_update)) == (200, {})

    dispatcher.feed_max_update.assert_awaited_once()


async def test_handle_request_rejects_unverified_unloadable_update() -> None:
    engine = DummyEngine(
        Dispatcher(),
        DummyAdapter(),
        bot=Bot("token"),
        security=Security(secret_token=StaticSecretToken("expected-secret")),
    )
    request = JsonBoundRequest(
        UNKNOWN_UPDATE_TYPE,
        DummyRequest(headers={SECRET_HEADER: "wrong-secret"}),
    )

    assert await engine.handle_request(request) == (403, {"detail": "Forbidden"})


NOT_UTF8_BODY = b"\x80abc"


class NotUtf8BoundRequest(DummyBoundRequest):
    async def json(self) -> dict[str, Any]:
        raise UnicodeDecodeError("utf-8", NOT_UTF8_BODY, 0, 1, "invalid start byte")


async def test_handle_request_returns_400_for_non_utf8_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=make_bot())

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        response = await engine.handle_request(NotUtf8BoundRequest())

    assert response == (400, {"detail": "Bad request"})
    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert caplog.records[0].exc_info is None


async def test_aiohttp_non_utf8_body_gets_400(
    aiohttp_client: AiohttpClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    engine = DummyEngine(Dispatcher(), AiohttpWebAdapter(), bot=Bot("token"))
    app = web.Application()
    engine.register(app)
    client = await aiohttp_client(app)
    caplog.clear()

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        response = await client.post(
            "/webhook",
            data=NOT_UTF8_BODY,
            headers={"Content-Type": "application/json"},
        )

    assert response.status == 400
    assert await response.json() == {"detail": "Bad request"}
    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_fastapi_non_utf8_body_gets_400(caplog: pytest.LogCaptureFixture) -> None:
    engine = DummyEngine(Dispatcher(), FastApiWebAdapter(), bot=Bot("token"))
    app = FastAPI()
    engine.register(app)
    client = TestClient(app)
    caplog.clear()

    with caplog.at_level(logging.WARNING, logger=loggers.webhook.name):
        response = client.post(
            "/webhook",
            content=NOT_UTF8_BODY,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Bad request"}
    assert [r.levelno for r in caplog.records] == [logging.WARNING]
