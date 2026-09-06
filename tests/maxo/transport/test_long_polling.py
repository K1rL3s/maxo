import asyncio
from asyncio import CancelledError
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from adaptix.load_error import LoadError

from maxo.backoff import BackoffConfig
from maxo.bot.api_client import MaxApiClient
from maxo.bot.bot import Bot
from maxo.bot.methods import GetUpdates
from maxo.bot.state import RunningBotState
from maxo.errors import UnsubscribeError
from maxo.omit import Omitted
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.shutdown import AfterShutdown, BeforeShutdown
from maxo.routing.signals.update import MaxoUpdate
from maxo.transport.long_polling import LongPolling
from maxo.types import (
    BotInfo,
    ClearSubscriptionsResult,
    GetSubscriptionsResult,
    MaxoType,
    Subscription,
    UpdateList,
)
from maxo.types.updates import Updates
from tests.factories import make_bot


@dataclass
class MockUpdate(MaxoType):
    timestamp: int = field(default=0)


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


async def anext_coro(generator: AsyncIterator[Any]) -> Any:
    return await anext(generator)


async def run_generator_once(generator: AsyncIterator[Any]) -> None:
    task = asyncio.create_task(anext_coro(generator))
    await asyncio.sleep(0.1)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def empty_updates(**_kwargs: Any) -> AsyncIterator[Any]:
    nothing: tuple[Any, ...] = ()
    for update in nothing:
        yield update


async def test_handles_load_error_and_skips_update(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_api_client: AsyncMock,
) -> None:
    initial_marker = 10
    mock_api_client.call_method.side_effect = [
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


@pytest.mark.parametrize(
    "types",
    [Omitted(), []],
    ids=["omitted", "empty-list"],
)
async def test_start_collects_used_updates_when_types_not_given(
    mock_bot: Bot,
    mock_get_subscriptions: AsyncMock,
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

    mock_get_subscriptions.assert_awaited_once_with()
    assert spy.call_args.kwargs["types"] == ["message_created"]


async def test_start_respects_explicit_types(
    mock_bot: Bot,
    mock_get_subscriptions: AsyncMock,
) -> None:
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

    mock_get_subscriptions.assert_awaited_once_with()
    assert spy.call_args.kwargs["types"] == ["bot_started"]


async def test_start_feeds_updates_to_dispatcher(
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_feed_max_update: AsyncMock,
    mock_get_subscriptions: AsyncMock,
) -> None:
    update = MaxoUpdate(update=cast(Updates, MockUpdate(timestamp=1)), marker=1)

    async def single_update(**_kwargs: Any) -> AsyncIterator[MaxoUpdate[Any]]:
        yield update

    with patch.object(long_polling, "_get_updates", side_effect=single_update):
        await long_polling.start(mock_bot, auto_close_bot=False)

    mock_get_subscriptions.assert_awaited_once_with()
    mock_feed_max_update.assert_awaited_once_with(update, mock_bot)


async def test_start_clears_subscriptions_when_requested(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    cleared = ClearSubscriptionsResult(
        removed=[
            Subscription(
                time=datetime.now(tz=UTC),
                url="https://example.com/webhook",
            ),
        ],
        kept=[],
    )

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
        patch.object(
            Bot,
            "clear_subscriptions",
            new=AsyncMock(return_value=cleared),
        ) as clear,
        patch.object(Bot, "get_subscriptions", new=AsyncMock()) as get,
        patch("maxo.transport.long_polling.loggers.long_polling") as logger,
    ):
        await long_polling.start(
            mock_bot,
            auto_close_bot=False,
            clear_subscriptions=True,
        )

    clear.assert_awaited_once_with()
    get.assert_not_awaited()
    logger.warning.assert_not_called()
    logger.info.assert_called_once_with(
        "Удалено WebHook-подписок перед запуском Long Polling (%d): %s",
        1,
        ["https://example.com/webhook"],
    )


async def test_start_fails_when_clear_subscriptions_fails(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    failure = ExceptionGroup(
        "Не удалось удалить WebHook-подписки",
        [UnsubscribeError(url="https://example.com/webhook", error=ValueError("boom"))],
    )
    get_updates = MagicMock(side_effect=empty_updates)

    with (
        patch.object(long_polling, "_get_updates", new=get_updates),
        patch.object(Bot, "clear_subscriptions", new=AsyncMock(side_effect=failure)),
        pytest.raises(ExceptionGroup),
    ):
        await long_polling.start(
            mock_bot,
            auto_close_bot=False,
            clear_subscriptions=True,
        )

    get_updates.assert_not_called()


async def test_start_clears_subscriptions_before_after_startup(
    mock_dispatcher: Dispatcher,
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    # Падение очистки не должно оставлять приложение со сработавшими
    # startup-хуками и несработавшими shutdown.
    fired: list[str] = []

    @mock_dispatcher.before_startup()
    async def _before_startup() -> None:
        fired.append("before_startup")

    @mock_dispatcher.after_startup()
    async def _after_startup() -> None:
        fired.append("after_startup")

    failure = ExceptionGroup(
        "Не удалось удалить WebHook-подписки",
        [UnsubscribeError(url="https://example.com/webhook", error=ValueError("boom"))],
    )

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
        patch.object(Bot, "clear_subscriptions", new=AsyncMock(side_effect=failure)),
        pytest.raises(ExceptionGroup),
    ):
        await long_polling.start(
            mock_bot,
            auto_close_bot=False,
            clear_subscriptions=True,
        )

    assert fired == ["before_startup"]


async def test_start_feeds_bot_to_after_shutdown(
    mock_dispatcher: Dispatcher,
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_get_subscriptions: AsyncMock,
) -> None:
    # `feed_signal(AfterShutdown())` was called with no `bot` at all, unlike
    # every other signal here (including this same method's own
    # `BeforeShutdown`) and unlike `SimpleWebhookEngine`'s `AfterShutdown`,
    # which does pass its bot. `feed_update` backfills `ctx["bot"]` from
    # `workflow_data` regardless, so a handler parameter named `bot` still
    # resolved either way - but `bot` not being passed also means
    # `feed_update` skips `ctx["bots"] = [bot]` and `update.bot = bot`, so a
    # handler reading the signal object's own `.bot` (as opposed to a `bot`
    # parameter) saw `None` instead of the real bot. Asserting on the actual
    # call to `feed_signal`, rather than on what a handler receives, is what
    # catches that - a handler-side assertion can't tell "backfilled from
    # workflow_data" apart from "passed explicitly".
    real_feed_signal = mock_dispatcher.feed_signal

    with (
        patch.object(
            mock_dispatcher,
            "feed_signal",
            new=AsyncMock(side_effect=real_feed_signal),
        ) as feed_signal,
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
    ):
        await long_polling.start(mock_bot, auto_close_bot=False)

    feed_signal.assert_any_call(ANY, mock_bot)
    shutdown_calls = [
        call_args
        for call_args in feed_signal.call_args_list
        if isinstance(call_args.args[0], (BeforeShutdown, AfterShutdown))
    ]
    assert shutdown_calls == [
        call(ANY, mock_bot),
        call(ANY, mock_bot),
    ]
    assert isinstance(shutdown_calls[0].args[0], BeforeShutdown)
    assert isinstance(shutdown_calls[1].args[0], AfterShutdown)


async def test_start_fires_shutdown_signals_when_polling_task_is_cancelled(
    mock_dispatcher: Dispatcher,
    long_polling: LongPolling,
    mock_bot: Bot,
    mock_get_subscriptions: AsyncMock,
) -> None:
    # `task.cancel()` on the task running `start()` is the standard way to stop
    # an application that catches its own shutdown signal (SIGTERM), per
    # AGENTS.md. That raises `CancelledError` out of the `TaskGroup`, which
    # `contextlib.suppress(KeyboardInterrupt)` does not catch - previously this
    # unwound straight out of `start()` and skipped both `before_shutdown` and
    # `after_shutdown` entirely, so nothing ever got to close the DB, flush
    # metrics or remove the webhook subscription on a cancelled shutdown.
    order: list[str] = []

    @mock_dispatcher.before_shutdown()
    async def _before_shutdown() -> None:
        order.append("before_shutdown")

    @mock_dispatcher.after_shutdown()
    async def _after_shutdown() -> None:
        order.append("after_shutdown")

    async def hanging_updates(**_kwargs: Any) -> AsyncIterator[Any]:
        await asyncio.sleep(60)
        nothing: tuple[Any, ...] = ()
        for update in nothing:
            yield update

    with patch.object(long_polling, "_get_updates", side_effect=hanging_updates):
        task = asyncio.create_task(
            long_polling.start(mock_bot, auto_close_bot=False),
        )
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(CancelledError):
            await task

    assert order == ["before_shutdown", "after_shutdown"]


async def test_start_warns_about_subscriptions_when_not_cleared(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(
                time=datetime.now(tz=UTC),
                url="https://example.com/webhook",
            ),
        ],
    )

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ) as get,
        patch.object(Bot, "clear_subscriptions", new=AsyncMock()) as clear,
        patch("maxo.transport.long_polling.loggers.long_polling") as logger,
    ):
        await long_polling.start(mock_bot, auto_close_bot=False)

    get.assert_awaited_once_with()
    clear.assert_not_awaited()
    logger.warning.assert_called_once_with(
        "У бота @%s есть активные WebHook-подписки (%d). "
        "Они не были очищены перед запуском Long Polling. "
        "Передайте clear_subscriptions=True, чтобы удалить их.",
        "test_bot",
        1,
    )


async def test_start_does_not_warn_when_there_are_no_subscriptions(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    subscriptions = GetSubscriptionsResult(subscriptions=[])

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates),
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ) as get,
        patch("maxo.transport.long_polling.loggers.long_polling") as logger,
    ):
        await long_polling.start(mock_bot, auto_close_bot=False)

    get.assert_awaited_once_with()
    logger.warning.assert_not_called()


async def test_start_continues_when_subscription_check_fails(
    long_polling: LongPolling,
    mock_bot: Bot,
) -> None:
    error = RuntimeError("API unavailable")

    with (
        patch.object(long_polling, "_get_updates", side_effect=empty_updates) as get,
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(side_effect=error),
        ) as get_subscriptions,
        patch("maxo.transport.long_polling.loggers.long_polling") as logger,
    ):
        await long_polling.start(mock_bot, auto_close_bot=False)

    get_subscriptions.assert_awaited_once_with()
    get.assert_called_once()
    logger.warning.assert_called_once_with(
        "Не удалось проверить WebHook-подписки перед запуском Long Polling - %s: %s",
        "RuntimeError",
        error,
    )


def test_run_passes_clear_subscriptions_to_start(mock_bot: Bot) -> None:
    long_polling = LongPolling(dispatcher=Dispatcher())

    with patch.object(long_polling, "start", new=AsyncMock()) as start:
        long_polling.run(
            mock_bot,
            auto_close_bot=False,
            clear_subscriptions=True,
        )

    start.assert_awaited_once_with(
        bot=mock_bot,
        timeout=30,
        limit=100,
        marker=Omitted(),
        types=Omitted(),
        auto_close_bot=False,
        drop_pending_updates=False,
        clear_subscriptions=True,
    )


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
            clear_subscriptions=True,
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
        clear_subscriptions=True,
        extra="context",
    )


async def test_start_polling_omits_types_by_default(mock_bot: Bot) -> None:
    dispatcher = Dispatcher()

    with patch.object(LongPolling, "start", new_callable=AsyncMock) as start:
        await dispatcher.start_polling(mock_bot)

    assert start.await_args is not None
    assert start.await_args.kwargs["types"] == Omitted()
    assert start.await_args.kwargs["clear_subscriptions"] is False


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
            clear_subscriptions=True,
            backoff_config=backoff_config,
        )

    init.assert_called_once_with(dispatcher, backoff_config=backoff_config)
    start.assert_awaited_once()
    assert start.await_args is not None
    assert start.await_args.kwargs["timeout"] == 7
    assert start.await_args.kwargs["auto_close_bot"] is False
    assert start.await_args.kwargs["clear_subscriptions"] is True
