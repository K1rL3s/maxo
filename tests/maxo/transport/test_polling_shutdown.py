import asyncio
from asyncio import CancelledError
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from maxo.bot.api_client import MaxApiClient
from maxo.bot.bot import Bot
from maxo.bot.state import RunningBotState
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.shutdown import AfterShutdown, BeforeShutdown
from maxo.transport.long_polling import LongPolling
from maxo.types import BotInfo, GetSubscriptionsResult
from tests.factories import make_bot


@pytest.fixture
def mock_api_client() -> AsyncMock:
    return AsyncMock(spec=MaxApiClient)


@pytest.fixture
def mock_bot(mock_api_client: AsyncMock) -> Bot:
    bot = make_bot()
    bot._state = RunningBotState(
        info=BotInfo(
            user_id=123,
            first_name="test_bot",
            username="test_bot",
            is_bot=True,
            last_activity_time=datetime.fromtimestamp(1234567890, tz=UTC),
        ),
        api_client=mock_api_client,
    )
    return bot


@pytest.fixture
def mock_get_subscriptions() -> Iterator[AsyncMock]:
    with patch.object(
        Bot,
        "get_subscriptions",
        new=AsyncMock(
            return_value=GetSubscriptionsResult(subscriptions=[]),
        ),
    ) as get_subscriptions:
        yield get_subscriptions


async def test_start_emits_shutdown_signals_when_polling_task_is_cancelled(
    mock_bot: Bot,
    mock_get_subscriptions: AsyncMock,
) -> None:
    dispatcher = Dispatcher()
    feed_signal = AsyncMock(wraps=dispatcher.feed_signal)
    dispatcher.feed_signal = feed_signal  # type: ignore[method-assign]

    @dispatcher.message_created()
    async def _handler(update: Any) -> None: ...

    long_polling = LongPolling(dispatcher=dispatcher)

    async def hang_forever(**_kwargs: Any) -> AsyncIterator[Any]:
        await asyncio.Future()
        if False:  # pragma: no cover
            yield None

    with patch.object(long_polling, "_get_updates", side_effect=hang_forever):
        task = asyncio.create_task(
            long_polling.start(mock_bot, auto_close_bot=False),
        )
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(CancelledError):
            await task

    signal_types = [type(call.args[0]) for call in feed_signal.await_args_list]
    assert BeforeShutdown in signal_types
    assert AfterShutdown in signal_types

    after_shutdown = next(
        call
        for call in feed_signal.await_args_list
        if isinstance(call.args[0], AfterShutdown)
    )
    assert after_shutdown.args[1] is mock_bot
