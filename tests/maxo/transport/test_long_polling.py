import asyncio
from asyncio import CancelledError
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import ANY, AsyncMock, call, patch

import pytest
from adaptix.load_error import LoadError

from maxo.bot.api_client import MaxApiClient
from maxo.bot.bot import Bot
from maxo.bot.methods import GetUpdates
from maxo.bot.state import RunningBotState
from maxo.omit import Omitted
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.update import MaxoUpdate
from maxo.transport.long_polling import LongPolling
from maxo.types import BotInfo, MaxoType, UpdateList


@dataclass
class MockUpdate(MaxoType):
    timestamp: int = field(default=0)


@pytest.fixture
def mock_api_client() -> AsyncMock:
    return AsyncMock(spec=MaxApiClient)


@pytest.fixture
def mock_bot(mock_api_client: AsyncMock) -> Bot:
    bot = Bot("test_token")
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
def mock_feed_max_update() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_dispatcher(mock_feed_max_update: AsyncMock) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.feed_max_update = mock_feed_max_update  # type: ignore[method-assign]
    return dispatcher


@pytest.fixture
def long_polling(mock_dispatcher: Dispatcher) -> LongPolling:
    return LongPolling(dispatcher=mock_dispatcher)


async def anext_coro(generator: AsyncIterator[Any]) -> Any:
    return await anext(generator)


async def run_generator_once(generator: AsyncIterator[Any]) -> None:
    task = asyncio.create_task(anext_coro(generator))
    await asyncio.sleep(0.1)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def test_handles_load_error_and_skips_update(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
) -> None:
    initial_marker = 10
    mock_api_client.call_method.side_effect = [
        LoadError("Test LoadError"),
        UpdateList(updates=[MockUpdate(timestamp=100)], marker=initial_marker + 2),
        CancelledError,
    ]

    with (
        patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger,
        patch("maxo.backoff.Backoff.next") as mock_backoff_next,
        patch(
            "maxo.backoff.Backoff.sleep",
            new_callable=AsyncMock,
        ) as mock_backoff_sleep,
    ):
        updates_generator = long_polling._get_updates(
            bot=mock_bot,
            marker=initial_marker,
        )

        first_yielded_update = await updates_generator.__anext__()

        mock_logger.exception.assert_called_once_with(
            "Ошибка загрузки апдейта в модель. "
            "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
        )
        assert mock_api_client.call_method.call_count == 2
        mock_api_client.call_method.assert_has_calls(
            [
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker,
                        timeout=30,
                        types=Omitted(),
                    ),
                ),
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker + 1,
                        timeout=30,
                        types=Omitted(),
                    ),
                ),
            ],
        )

        assert isinstance(first_yielded_update, MaxoUpdate)
        assert isinstance(first_yielded_update.update, MockUpdate)
        assert first_yielded_update.update.timestamp == 100
        assert first_yielded_update.marker == initial_marker + 2

        mock_backoff_next.assert_not_called()
        mock_backoff_sleep.assert_not_called()

        with pytest.raises(CancelledError):
            await updates_generator.__anext__()


async def test_handles_load_error_with_no_marker(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
) -> None:
    mock_api_client.call_method.side_effect = [
        LoadError("Test LoadError"),
        CancelledError,
    ]

    with (
        patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger,
        patch("maxo.backoff.Backoff.next") as mock_backoff_next,
        patch(
            "maxo.backoff.Backoff.sleep",
            new_callable=AsyncMock,
        ) as mock_backoff_sleep,
    ):
        updates_generator = long_polling._get_updates(bot=mock_bot, marker=None)

        with pytest.raises(CancelledError):
            await updates_generator.__anext__()

        mock_logger.exception.assert_called_once_with(
            "Ошибка загрузки апдейта в модель. "
            "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
        )
        assert mock_api_client.call_method.call_count == 2
        mock_backoff_next.assert_called_once()
        mock_backoff_sleep.assert_called_once()


async def test_handles_general_exception(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_dispatcher: Dispatcher,
    mock_api_client: AsyncMock,
    mock_feed_max_update: AsyncMock,
) -> None:
    mock_api_client.call_method.side_effect = ValueError(
        "Test ValueError",
    )

    with patch("maxo.transport.long_polling.loggers.dispatcher") as mock_logger:
        updates_generator = long_polling._get_updates(bot=mock_bot)

        await run_generator_once(updates_generator)

        mock_logger.exception.assert_called_once_with(
            "Failed to fetch updates - %s: %s",
            "ValueError",
            ANY,
        )
        mock_api_client.call_method.assert_called_once()
        mock_feed_max_update.assert_not_called()
