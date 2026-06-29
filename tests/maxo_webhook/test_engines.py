from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.bot.bot import Bot
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook.engines.simple import SimpleEngine


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
