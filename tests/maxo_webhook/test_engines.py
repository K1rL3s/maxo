import asyncio
import logging
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import loggers
from maxo.bot.bot import Bot
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.engines.simple import SimpleEngine

from .fixtures import DummyAdapter, DummyBoundRequest


class TestSimpleEngine:
    @pytest.fixture
    def dispatcher(self) -> Dispatcher:
        return Dispatcher()

    @pytest.fixture
    def bot(self) -> MagicMock:
        return MagicMock(spec=Bot)

    @pytest.fixture
    def web_adapter(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def routing(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def security(self) -> MagicMock:
        security = MagicMock()
        security.get_secret_token = AsyncMock(return_value="secret")
        return security

    @pytest.fixture
    def engine(
        self,
        dispatcher: Dispatcher,
        bot: MagicMock,
        web_adapter: MagicMock,
        routing: MagicMock,
        security: MagicMock,
    ) -> SimpleEngine:
        return SimpleEngine(
            dispatcher,
            bot,
            web_adapter=web_adapter,
            routing=routing,
            security=security,
        )

    def test_get_bot_from_request(self, engine: SimpleEngine, bot: MagicMock) -> None:
        assert engine._get_bot_from_request(MagicMock()) is bot

    async def test_set_webhook(
        self,
        engine: SimpleEngine,
        bot: MagicMock,
        routing: MagicMock,
    ) -> None:
        routing.webhook_point.return_value = "https://example.com/webhook"
        bot.subscribe = AsyncMock()

        await engine.set_webhook(
            update_types=["message"],
        )

        bot.subscribe.assert_called_once()
        call_kwargs = bot.subscribe.call_args.kwargs
        assert call_kwargs["url"] == "https://example.com/webhook"
        assert call_kwargs["update_types"] == ["message"]

    async def test_on_startup(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
    ) -> None:
        feed_signal_mock = AsyncMock()
        dispatcher.feed_signal = feed_signal_mock  # type: ignore[method-assign]
        await engine.on_startup(app=MagicMock())
        assert dispatcher.feed_signal.await_count == 2
        assert isinstance(
            dispatcher.feed_signal.await_args_list[0].args[0],
            BeforeStartup,
        )
        assert isinstance(
            dispatcher.feed_signal.await_args_list[1].args[0],
            AfterStartup,
        )

    async def test_on_shutdown(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
        bot: MagicMock,
    ) -> None:
        feed_signal_mock = AsyncMock()
        dispatcher.feed_signal = feed_signal_mock  # type: ignore[method-assign]
        bot.close = AsyncMock()
        await engine.on_shutdown(app=MagicMock())
        assert dispatcher.feed_signal.await_count == 2
        bot.close.assert_awaited_once()
        assert isinstance(
            dispatcher.feed_signal.await_args_list[0].args[0],
            BeforeShutdown,
        )
        assert isinstance(
            dispatcher.feed_signal.await_args_list[1].args[0],
            AfterShutdown,
        )


class TestSimpleEngineShutdown:
    @pytest.fixture
    def events(self) -> list[str]:
        return []

    @pytest.fixture
    def release(self) -> asyncio.Event:
        return asyncio.Event()

    @pytest.fixture
    def dispatcher(self, events: list[str], release: asyncio.Event) -> Dispatcher:
        async def feed_max_update(**kwargs: Any) -> None:
            events.append("handler started")
            try:
                await release.wait()
            except asyncio.CancelledError:
                events.append("handler cancelled")
                raise
            events.append("handler finished")

        async def feed_signal(signal: Any, *args: Any) -> None:
            events.append(type(signal).__name__)

        dispatcher = Dispatcher()
        dispatcher.feed_max_update = AsyncMock(  # type: ignore[method-assign]
            side_effect=feed_max_update,
        )
        dispatcher.feed_signal = AsyncMock(  # type: ignore[method-assign]
            side_effect=feed_signal,
        )
        return dispatcher

    @pytest.fixture
    def bot(self, events: list[str]) -> MagicMock:
        async def close() -> None:
            events.append("bot closed")

        bot = MagicMock(spec=Bot)
        bot.close = AsyncMock(side_effect=close)
        bot.start = AsyncMock()
        return bot

    @pytest.fixture
    def security(self) -> MagicMock:
        security = MagicMock()
        security.verify = AsyncMock(return_value=True)
        return security

    @pytest.fixture
    def engine(
        self,
        dispatcher: Dispatcher,
        bot: MagicMock,
        security: MagicMock,
    ) -> SimpleEngine:
        return SimpleEngine(
            dispatcher,
            bot,
            web_adapter=DummyAdapter(),
            routing=MagicMock(),
            security=security,
            shutdown_timeout=5,
        )

    async def test_shutdown_waits_for_background_handler(
        self,
        engine: SimpleEngine,
        events: list[str],
        release: asyncio.Event,
    ) -> None:
        assert await engine.handle_request(DummyBoundRequest()) == (200, {})
        await asyncio.sleep(0)

        shutdown = asyncio.create_task(engine.on_shutdown(app=MagicMock()))
        await asyncio.sleep(0.01)
        assert not shutdown.done()
        assert events == ["handler started"]

        release.set()
        await shutdown

        assert events == [
            "handler started",
            "handler finished",
            "BeforeShutdown",
            "bot closed",
            "AfterShutdown",
        ]

    async def test_shutdown_cancels_handler_after_timeout(
        self,
        engine: SimpleEngine,
        events: list[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        engine.shutdown_timeout = 0.01
        await engine.handle_request(DummyBoundRequest())

        with caplog.at_level(logging.WARNING, logger=loggers.webhook_tasks.name):
            await asyncio.wait_for(engine.on_shutdown(app=MagicMock()), timeout=1)

        assert events == [
            "handler started",
            "handler cancelled",
            "BeforeShutdown",
            "bot closed",
            "AfterShutdown",
        ]
        assert [(r.name, r.levelno) for r in caplog.records] == [
            (loggers.webhook_tasks.name, logging.WARNING),
        ]

    async def test_request_during_shutdown_returns_503(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
        release: asyncio.Event,
    ) -> None:
        await engine.handle_request(DummyBoundRequest())
        shutdown = asyncio.create_task(engine.on_shutdown(app=MagicMock()))
        await asyncio.sleep(0)

        assert await engine.handle_request(DummyBoundRequest()) == (
            503,
            {"detail": "Service unavailable"},
        )

        release.set()
        await shutdown
        assert dispatcher.feed_max_update.await_count == 1  # type: ignore[attr-defined]

    @pytest.mark.parametrize("handle_in_background", [True, False])
    async def test_shutdown_started_during_request_spawns_nothing(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
        security: MagicMock,
        events: list[str],
        release: asyncio.Event,
        handle_in_background: bool,
    ) -> None:
        engine.handle_in_background = handle_in_background
        release.set()
        verified = asyncio.Event()
        verify_release = asyncio.Event()

        async def verify(**kwargs: Any) -> bool:
            verified.set()
            await verify_release.wait()
            return True

        security.verify.side_effect = verify
        request = asyncio.create_task(engine.handle_request(DummyBoundRequest()))
        await verified.wait()

        await engine.on_shutdown(app=MagicMock())
        verify_release.set()

        assert await request == (503, {"detail": "Service unavailable"})
        await asyncio.sleep(0.01)
        dispatcher.feed_max_update.assert_not_awaited()  # type: ignore[attr-defined]
        assert events == ["BeforeShutdown", "bot closed", "AfterShutdown"]

    async def test_foreground_request_after_shutdown_returns_503(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
        security: MagicMock,
    ) -> None:
        engine.handle_in_background = False
        await engine.on_shutdown(app=MagicMock())

        response = engine.handle_request(DummyBoundRequest())
        assert await asyncio.wait_for(response, timeout=1) == (
            503,
            {"detail": "Service unavailable"},
        )
        security.verify.assert_not_awaited()
        dispatcher.feed_max_update.assert_not_awaited()  # type: ignore[attr-defined]

    async def test_startup_accepts_requests_after_shutdown(
        self,
        engine: SimpleEngine,
        release: asyncio.Event,
    ) -> None:
        release.set()
        await engine.on_shutdown(app=MagicMock())
        await engine.on_startup(app=MagicMock())

        assert await engine.handle_request(DummyBoundRequest()) == (200, {})

    async def test_background_handler_error_is_logged(
        self,
        engine: SimpleEngine,
        dispatcher: Dispatcher,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        dispatcher.feed_max_update.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]

        with caplog.at_level(logging.ERROR, logger=loggers.webhook_tasks.name):
            assert await engine.handle_request(DummyBoundRequest()) == (200, {})
            await engine.on_shutdown(app=MagicMock())

        assert [(r.name, r.levelno) for r in caplog.records] == [
            (loggers.webhook_tasks.name, logging.ERROR),
        ]
        exc_info = caplog.records[0].exc_info
        assert exc_info is not None
        assert isinstance(exc_info[1], RuntimeError)


class CustomEngine(WebhookEngine):
    def __init__(self, *args: Any, bot: Bot, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot

    def _get_bot_from_request(self, bound_request: BoundRequest[Any]) -> Bot | None:
        return self.bot

    async def set_webhook(self, *args: Any, **kwargs: Any) -> Bot:
        return self.bot

    async def on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        self._is_shutting_down = False

    async def on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        await self._stop_background_tasks()


class TestCustomEngineShutdown:
    @pytest.fixture
    def release(self) -> asyncio.Event:
        return asyncio.Event()

    @pytest.fixture
    def dispatcher(self, release: asyncio.Event) -> Dispatcher:
        async def feed_max_update(**kwargs: Any) -> None:
            await release.wait()

        dispatcher = Dispatcher()
        dispatcher.feed_max_update = AsyncMock(  # type: ignore[method-assign]
            side_effect=feed_max_update,
        )
        return dispatcher

    @pytest.fixture
    def engine(self, dispatcher: Dispatcher) -> CustomEngine:
        security = MagicMock()
        security.verify = AsyncMock(return_value=True)
        return CustomEngine(
            dispatcher,
            bot=MagicMock(spec=Bot),
            web_adapter=DummyAdapter(),
            routing=MagicMock(),
            security=security,
            shutdown_timeout=5,
        )

    async def test_stop_background_tasks_rejects_requests_and_waits(
        self,
        engine: CustomEngine,
        dispatcher: Dispatcher,
        release: asyncio.Event,
    ) -> None:
        assert await engine.handle_request(DummyBoundRequest()) == (200, {})
        await asyncio.sleep(0)

        shutdown = asyncio.create_task(engine.on_shutdown(app=MagicMock()))
        await asyncio.sleep(0.01)
        assert not shutdown.done()
        assert await engine.handle_request(DummyBoundRequest()) == (
            503,
            {"detail": "Service unavailable"},
        )

        release.set()
        await shutdown
        assert dispatcher.feed_max_update.await_count == 1  # type: ignore[attr-defined]

    async def test_stop_background_tasks_cancels_after_timeout(
        self,
        engine: CustomEngine,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        engine.shutdown_timeout = 0.01
        await engine.handle_request(DummyBoundRequest())
        await asyncio.sleep(0)

        with caplog.at_level(logging.WARNING, logger=loggers.webhook_tasks.name):
            await asyncio.wait_for(engine.on_shutdown(app=MagicMock()), timeout=1)

        assert [(r.name, r.levelno) for r in caplog.records] == [
            (loggers.webhook_tasks.name, logging.WARNING),
        ]
