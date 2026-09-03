import asyncio
import contextlib
import time
from collections.abc import AsyncIterator, Sequence
from typing import Any

from adaptix.load_error import LoadError

from maxo import loggers
from maxo.backoff import Backoff, BackoffConfig
from maxo.bot.bot import Bot
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals.shutdown import AfterShutdown, BeforeShutdown
from maxo.routing.signals.startup import AfterStartup, BeforeStartup
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.utils import collect_used_updates

_DEFAULT_BACKOFF_CONFIG = BackoffConfig(
    min_delay=1.0,
    max_delay=5.0,
    factor=1.3,
    jitter=0.1,
)


class LongPolling:
    def __init__(
        self,
        dispatcher: Dispatcher,
        backoff_config: BackoffConfig = _DEFAULT_BACKOFF_CONFIG,
    ) -> None:
        self._dispatcher = dispatcher
        self._backoff_config = backoff_config
        self._lock = asyncio.Lock()

    def run(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[Sequence[str]] = Omitted(),
        auto_close_bot: bool = True,
        drop_pending_updates: bool = False,
        clear_subscriptions: bool = False,
        **workflow_data: Any,
    ) -> None:
        asyncio.run(
            self.start(
                bot=bot,
                timeout=timeout,
                limit=limit,
                marker=marker,
                types=types,
                auto_close_bot=auto_close_bot,
                drop_pending_updates=drop_pending_updates,
                clear_subscriptions=clear_subscriptions,
                **workflow_data,
            ),
        )

    async def start(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[Sequence[str]] = Omitted(),
        auto_close_bot: bool = True,
        drop_pending_updates: bool = False,
        clear_subscriptions: bool = False,
        **workflow_data: Any,
    ) -> None:
        dispatcher = self._dispatcher
        used_types: list[str] = list(
            types if is_defined(types) and types else collect_used_updates(dispatcher),
        )

        async with self._lock:
            dispatcher.workflow_data.update(bot=bot, **workflow_data)

            await dispatcher.feed_signal(BeforeStartup(), bot)

            async with bot.context(auto_close=auto_close_bot):
                loggers.dispatcher.info(
                    "Polling started for @%s id=%s",
                    bot.state.info.username,
                    bot.state.info.user_id,
                )

                if clear_subscriptions:
                    cleared = await bot.clear_subscriptions()
                    loggers.long_polling.info(
                        "Удалено WebHook-подписок перед запуском "
                        "Long Polling (%d): %s",
                        len(cleared.removed),
                        [subscription.url for subscription in cleared.removed],
                    )
                else:
                    try:
                        subscriptions = await bot.get_subscriptions()
                    except Exception as exception:  # noqa: BLE001
                        loggers.long_polling.warning(
                            "Не удалось проверить WebHook-подписки перед "
                            "запуском Long Polling - %s: %s",
                            type(exception).__name__,
                            exception,
                        )
                    else:
                        if subscriptions.subscriptions:
                            loggers.long_polling.warning(
                                "У бота @%s есть активные WebHook-подписки (%d). "
                                "Они не были очищены перед запуском Long Polling. "
                                "Передайте clear_subscriptions=True, чтобы удалить их.",
                                bot.state.info.username,
                                len(subscriptions.subscriptions),
                            )

                await dispatcher.feed_signal(AfterStartup(), bot)

                updates_poller = self._get_updates(
                    bot=bot,
                    timeout=timeout,
                    limit=limit,
                    marker=marker,
                    types=used_types,
                    drop_pending_updates=drop_pending_updates,
                )

                with contextlib.suppress(KeyboardInterrupt):
                    async with asyncio.TaskGroup() as tg:
                        async for update in updates_poller:
                            tg.create_task(  # type: ignore[unused-awaitable]
                                dispatcher.feed_max_update(update, bot),
                            )

                await dispatcher.feed_signal(BeforeShutdown(), bot)

                loggers.dispatcher.info(
                    "Polling stop for @%s bot id=%s",
                    bot.state.info.username,
                    bot.state.info.user_id,
                )

        await dispatcher.feed_signal(AfterShutdown())

    async def _get_updates(
        self,
        bot: Bot,
        timeout: Omittable[int] = 30,
        limit: Omittable[int] = 100,
        marker: Omittable[int | None] = Omitted(),
        types: Omittable[list[str]] = Omitted(),
        drop_pending_updates: bool = False,
    ) -> AsyncIterator[MaxoUpdate[Any]]:
        start_time = time.time()
        backoff = Backoff(self._backoff_config)
        bot_id = bot.state.info.user_id
        bot_username = bot.state.info.username

        failed = False
        while True:
            try:
                result = await bot.get_updates(
                    limit=limit,
                    timeout=timeout,
                    marker=marker,
                    types=types,
                )
            except LoadError:
                loggers.dispatcher.exception(
                    "Ошибка загрузки апдейта в модель. "
                    "Сообщите об этой ошибке в https://github.com/K1rL3s/maxo/issues",
                )
                if is_defined(marker):
                    marker += 1
                    continue

                failed = True
                backoff.next()
                loggers.dispatcher.warning(
                    "Первый запрос на получение обновлений не удался. "
                    "Sleep for %f seconds and try again... "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.current_delay,
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                await backoff.sleep()
                continue
            except Exception as exception:  # noqa: BLE001
                failed = True
                loggers.dispatcher.exception(
                    "Failed to fetch updates - %s: %s",
                    type(exception).__name__,
                    exception,
                )
                backoff.next()
                loggers.dispatcher.warning(
                    "Sleep for %f seconds and try again... "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.current_delay,
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                await backoff.sleep()
                continue

            if failed:
                loggers.dispatcher.info(
                    "Connection established "
                    "(tryings = %d, username = @%s, bot id = %d)",
                    backoff.counter,
                    bot_username,
                    bot_id,
                )
                backoff.reset()
                failed = False

            marker = result.marker

            for update in result.updates:
                if drop_pending_updates and update.timestamp.timestamp() < start_time:
                    loggers.long_polling.debug("Skip pending update: %s", update)
                    continue
                loggers.long_polling.debug("New update: %s", update)
                yield MaxoUpdate(update=update, marker=result.marker)
