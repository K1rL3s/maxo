from json import JSONDecodeError
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from adaptix.load_error import LoadError

from maxo import Bot, Dispatcher
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.engines import base as engine_base
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security
from maxo.types import Updates

from .fixtures import DummyAdapter, DummyBoundRequest, DummyRequest


@pytest.fixture(autouse=True)
def retort(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """
    Движок грузит апдейт через модульный `get_retort()`, а не `bot.retort`.

    Костыль после отказа от `create_retort_with_bot`: подменяем ретортом-моком.
    """
    retort_mock = MagicMock()
    retort_mock.load.return_value = MagicMock(spec=Updates)
    monkeypatch.setattr(engine_base, "get_retort", lambda: retort_mock)
    return retort_mock


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


def make_bot() -> MagicMock:
    bot = MagicMock(spec=Bot)
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


async def test_handle_request_returns_400_for_load_error(retort: MagicMock) -> None:
    retort.load.side_effect = LoadError
    bot = make_bot()
    engine = DummyEngine(Dispatcher(), DummyAdapter(), bot=bot)

    assert await engine.handle_request(JsonBoundRequest({"bad": "payload"})) == (
        400,
        {"detail": "Bad request"},
    )
    retort.load.assert_called_once_with({"bad": "payload"}, Updates)


async def test_handle_request_dispatches_update(retort: MagicMock) -> None:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = AsyncMock(return_value=None)  # type: ignore[method-assign]
    update = MagicMock(spec=Updates)
    retort.load.return_value = update
    bot = make_bot()
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
