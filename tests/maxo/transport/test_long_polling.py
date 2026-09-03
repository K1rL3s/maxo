import asyncio
from asyncio import CancelledError
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, cast
from unittest.mock import ANY, AsyncMock, call, patch

import pytest
from adaptix.load_error import LoadError

from maxo.backoff import BackoffConfig
from maxo.bot.bot import Bot
from maxo.bot.methods import GetUpdates
from maxo.omit import Omitted
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.update import MaxoUpdate
from maxo.transport.long_polling import LongPolling
from maxo.types import MaxoType, UpdateList
from maxo.types.updates import Updates
from tests.factories import make_bot, make_bot_info


@dataclass
class MockUpdate(MaxoType):
    timestamp: int = field(default=0)


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot(mock_client: AsyncMock) -> Bot:
    bot = make_bot(client=mock_client)
    bot._info = make_bot_info()
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
    mock_client: AsyncMock,
) -> None:
    initial_marker = 10
    mock_client.call_method.side_effect = [
        LoadError("Test LoadError"),
        UpdateList(
            updates=cast(list[Updates], [MockUpdate(timestamp=100)]),
            marker=initial_marker + 2,
        ),
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
        assert mock_client.call_method.call_count == 2
        mock_client.call_method.assert_has_calls(
            [
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker,
                        timeout=30,
                        types=Omitted(),
                    ),
                    middleware=ANY,
                ),
                call(
                    GetUpdates(
                        limit=100,
                        marker=initial_marker + 1,
                        timeout=30,
                        types=Omitted(),
                    ),
                    middleware=ANY,
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
    mock_client: AsyncMock,
) -> None:
    mock_client.call_method.side_effect = [
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
        assert mock_client.call_method.call_count == 2
        mock_backoff_next.assert_called_once()
        mock_backoff_sleep.assert_called_once()


async def test_handles_general_exception(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_client: AsyncMock,
    mock_feed_max_update: AsyncMock,
) -> None:
    mock_client.call_method.side_effect = ValueError(
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
        mock_client.call_method.assert_called_once()
        mock_feed_max_update.assert_not_called()


async def empty_updates(**_kwargs: Any) -> AsyncIterator[Any]:
    nothing: tuple[Any, ...] = ()
    for update in nothing:
        yield update


@pytest.mark.parametrize(
    "types",
    [Omitted(), []],
    ids=["omitted", "empty-list"],
)
async def test_start_collects_used_updates_when_types_not_given(
    mock_bot: Bot,
    types: Any,
) -> None:
    # Пустой список, как и Omitted(), означает "посчитать по роутерам",
    # иначе бот молча перестаёт получать апдейты
    dispatcher = Dispatcher()

    @dispatcher.message_created()
    async def _handler(update: Any) -> None: ...

    long_polling = LongPolling(dispatcher=dispatcher)

    with patch.object(long_polling, "_get_updates", side_effect=empty_updates) as spy:
        await long_polling.start(mock_bot, types=types, auto_close_bot=False)

    assert spy.call_args.kwargs["types"] == ["message_created"]


async def test_start_respects_explicit_types(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()

    @dispatcher.message_created()
    async def _handler(update: Any) -> None: ...

    long_polling = LongPolling(dispatcher=dispatcher)

    with patch.object(long_polling, "_get_updates", side_effect=empty_updates) as spy:
        await long_polling.start(
            mock_bot,
            types=["bot_started"],
            auto_close_bot=False,
        )

    assert spy.call_args.kwargs["types"] == ["bot_started"]


async def test_start_feeds_updates_to_dispatcher(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_feed_max_update: AsyncMock,
) -> None:
    update = MaxoUpdate(update=cast(Updates, MockUpdate(timestamp=1)), marker=1)

    async def single_update(**_kwargs: Any) -> AsyncIterator[MaxoUpdate[Any]]:
        yield update

    with patch.object(long_polling, "_get_updates", side_effect=single_update):
        await long_polling.start(mock_bot, auto_close_bot=False)

    mock_feed_max_update.assert_awaited_once_with(update, mock_bot)


async def test_start_polling_delegates_to_long_polling(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()
    backoff_config = BackoffConfig(
        min_delay=0.1,
        max_delay=1.0,
        factor=2.0,
        jitter=0.1,
    )

    with (
        patch.object(LongPolling, "__init__", return_value=None) as init,
        patch.object(LongPolling, "start", new_callable=AsyncMock) as start,
    ):
        await dispatcher.start_polling(
            mock_bot,
            timeout=5,
            limit=10,
            types=["message_created"],
            auto_close_bot=False,
            drop_pending_updates=True,
            backoff_config=backoff_config,
            extra="context",
        )

    init.assert_called_once_with(dispatcher, backoff_config=backoff_config)
    start.assert_awaited_once_with(
        bot=mock_bot,
        timeout=5,
        limit=10,
        marker=Omitted(),
        types=["message_created"],
        auto_close_bot=False,
        drop_pending_updates=True,
        extra="context",
    )


async def test_start_polling_omits_types_by_default(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()

    with patch.object(LongPolling, "start", new_callable=AsyncMock) as start:
        await dispatcher.start_polling(mock_bot)

    assert start.await_args is not None
    assert start.await_args.kwargs["types"] == Omitted()


def test_run_polling_runs_start_polling(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()
    backoff_config = BackoffConfig(
        min_delay=0.1,
        max_delay=1.0,
        factor=2.0,
        jitter=0.1,
    )

    with (
        patch.object(LongPolling, "__init__", return_value=None) as init,
        patch.object(LongPolling, "start", new_callable=AsyncMock) as start,
    ):
        dispatcher.run_polling(
            mock_bot,
            timeout=7,
            auto_close_bot=False,
            backoff_config=backoff_config,
        )

    init.assert_called_once_with(dispatcher, backoff_config=backoff_config)
    start.assert_awaited_once()
    assert start.await_args is not None
    assert start.await_args.kwargs["timeout"] == 7
    assert start.await_args.kwargs["auto_close_bot"] is False
