import asyncio
import logging
from json import JSONDecodeError
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from adaptix.load_error import LoadError

from maxo import Bot, Dispatcher
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security
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


async def test_handle_request_returns_400_for_load_error() -> None:
    bot = make_bot(load_error=True)
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=bot)

    assert await engine.handle_request(JsonBoundRequest({"bad": "payload"})) == (
        400,
        {"detail": "Bad request"},
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
    assert len(engine._background_feed_update_tasks) == 1

    task = next(iter(engine._background_feed_update_tasks))
    await task

    assert engine._background_feed_update_tasks == set()


async def test_drain_background_tasks_waits_pending_updates() -> None:
    dispatcher = Dispatcher()
    finished = asyncio.Event()

    async def slow_feed(*args: Any, **kwargs: Any) -> None:
        await asyncio.sleep(0.01)
        finished.set()

    dispatcher.feed_max_update = slow_feed  # type: ignore[method-assign]
    engine = DummyEngine(
        dispatcher,
        DummyAdapter(),
        bot=make_bot(),
        handle_in_background=True,
    )

    await engine.handle_request(JsonBoundRequest({"update": "payload"}))
    assert len(engine._background_feed_update_tasks) == 1

    await engine._drain_background_feed_update_tasks()

    assert finished.is_set()
    assert engine._background_feed_update_tasks == set()


async def test_drain_background_tasks_without_tasks_is_noop() -> None:
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=make_bot())

    await engine._drain_background_feed_update_tasks()

    assert engine._background_feed_update_tasks == set()


async def test_background_task_error_is_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    dispatcher = Dispatcher()

    async def failing_feed(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("boom")

    dispatcher.feed_max_update = failing_feed  # type: ignore[method-assign]
    engine = DummyEngine(
        dispatcher,
        DummyAdapter(),
        bot=make_bot(),
        handle_in_background=True,
    )

    with caplog.at_level(logging.ERROR, logger="maxo.webhook"):
        await engine.handle_request(JsonBoundRequest({"update": "payload"}))
        await engine._drain_background_feed_update_tasks()

    assert engine._background_feed_update_tasks == set()
    assert any(
        record.exc_info and isinstance(record.exc_info[1], RuntimeError)
        for record in caplog.records
    )


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
