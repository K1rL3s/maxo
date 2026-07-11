from typing import cast
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
from maxo.transport.webhook.engines import token as token_module
from maxo.transport.webhook.engines.token import TokenEngine


class TestTokenEngine:
    @pytest.fixture
    def dispatcher(self) -> Dispatcher:
        return Dispatcher()

    @pytest.fixture
    def web_adapter(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def routing(self) -> MagicMock:
        routing = MagicMock()
        routing.extract_token.return_value = "token-1"
        routing.webhook_point.return_value = "https://example.com/webhook"
        return routing

    @pytest.fixture
    def security(self) -> MagicMock:
        security = MagicMock()
        security.get_secret_token = AsyncMock(return_value="secret")
        return security

    @pytest.fixture
    def fake_bot_factory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _make(token: str, **_: object) -> MagicMock:
            bot = MagicMock(spec=Bot)
            bot.token = token
            bot.subscribe = AsyncMock()
            bot.start = AsyncMock()
            bot.close = AsyncMock()
            return bot

        monkeypatch.setattr(token_module, "Bot", MagicMock(side_effect=_make))

    @pytest.fixture
    def engine(
        self,
        dispatcher: Dispatcher,
        web_adapter: MagicMock,
        routing: MagicMock,
        security: MagicMock,
        fake_bot_factory: None,
    ) -> TokenEngine:
        return TokenEngine(
            dispatcher,
            web_adapter=web_adapter,
            routing=routing,
            security=security,
        )

    def test_get_bot_caches_by_token(self, engine: TokenEngine) -> None:
        bot1 = engine.get_bot("token-1")
        bot2 = engine.get_bot("token-1")
        bot3 = engine.get_bot("token-2")

        assert bot1 is bot2
        assert bot1 is not bot3
        assert bot1.token == "token-1"  # noqa: S105
        assert bot3.token == "token-2"  # noqa: S105

    def test_get_bot_from_request(
        self,
        engine: TokenEngine,
        routing: MagicMock,
    ) -> None:
        bot = engine._get_bot_from_request(MagicMock())
        assert bot is not None
        assert bot.token == "token-1"  # noqa: S105
        routing.extract_token.assert_called_once()

    def test_get_bot_from_request_no_token(
        self,
        engine: TokenEngine,
        routing: MagicMock,
    ) -> None:
        routing.extract_token.return_value = None
        assert engine._get_bot_from_request(MagicMock()) is None

    async def test_set_webhook(self, engine: TokenEngine) -> None:
        bot = cast(
            MagicMock,
            await engine.set_webhook("token-1", update_types=["message_created"]),
        )

        bot.subscribe.assert_awaited_once()
        call_kwargs = bot.subscribe.call_args.kwargs
        assert call_kwargs["url"] == "https://example.com/webhook"
        assert call_kwargs["secret"] == "secret"  # noqa: S105
        assert call_kwargs["update_types"] == ["message_created"]

    async def test_on_startup_starts_all_bots(
        self,
        engine: TokenEngine,
        dispatcher: Dispatcher,
    ) -> None:
        feed_signal_mock = AsyncMock()
        dispatcher.feed_signal = feed_signal_mock  # type: ignore[method-assign]
        bot_a = cast(MagicMock, engine.get_bot("token-1"))
        bot_b = cast(MagicMock, engine.get_bot("token-2"))

        await engine.on_startup(app=MagicMock())

        bot_a.start.assert_awaited_once()
        bot_b.start.assert_awaited_once()
        assert dispatcher.feed_signal.await_count == 2
        assert isinstance(
            dispatcher.feed_signal.await_args_list[0].args[0],
            BeforeStartup,
        )
        assert isinstance(
            dispatcher.feed_signal.await_args_list[1].args[0],
            AfterStartup,
        )

    async def test_on_startup_includes_extra_bots(
        self,
        engine: TokenEngine,
        dispatcher: Dispatcher,
    ) -> None:
        dispatcher.feed_signal = AsyncMock()  # type: ignore[method-assign]
        extra = MagicMock(spec=Bot)
        extra.token = "extra-token"  # noqa: S105
        extra.start = AsyncMock()

        await engine.on_startup(app=MagicMock(), bots={extra})

        extra.start.assert_awaited_once()
        assert engine.get_bot("extra-token") is extra

    async def test_on_shutdown_closes_and_clears_bots(
        self,
        engine: TokenEngine,
        dispatcher: Dispatcher,
    ) -> None:
        feed_signal_mock = AsyncMock()
        dispatcher.feed_signal = feed_signal_mock  # type: ignore[method-assign]
        bot_a = cast(MagicMock, engine.get_bot("token-1"))

        await engine.on_shutdown(app=MagicMock())

        bot_a.close.assert_awaited_once()
        assert engine._bots == {}
        assert dispatcher.feed_signal.await_count == 2
        assert isinstance(
            dispatcher.feed_signal.await_args_list[0].args[0],
            BeforeShutdown,
        )
        assert isinstance(
            dispatcher.feed_signal.await_args_list[1].args[0],
            AfterShutdown,
        )
