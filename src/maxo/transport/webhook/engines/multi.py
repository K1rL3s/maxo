from abc import ABC
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Any, Generic

from maxo import Bot, Dispatcher
from maxo.loggers import webhook
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook import WebhookConfig
from maxo.transport.webhook.engines.base import (
    AppT,
    BaseWebhookEngine,
    FrameworkResponseT,
    RawRequestT,
)
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.security import Security
from maxo.transport.webhook.tasks import TaskTracker
from maxo.transport.webhook.web.base import WebAdapter


class BaseMultiBotEngine(
    BaseWebhookEngine[AppT, RawRequestT, FrameworkResponseT],
    ABC,
    Generic[AppT, RawRequestT, FrameworkResponseT],
):
    def __init__(
        self,
        dispatcher: Dispatcher,
        web: WebAdapter[AppT, RawRequestT, FrameworkResponseT],
        route: Route,
        security: Security | None = None,
        webhook_config: WebhookConfig | None = None,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self._task_trackers: dict[int, TaskTracker] = {}
        self._bots: dict[int, Bot] = {}
        self.webhook_config = webhook_config or WebhookConfig()
        super().__init__(
            dispatcher=dispatcher,
            web=web,
            route=route,
            security=security,
            shutdown_timeout=shutdown_timeout,
        )

    @property
    def bots(self) -> Mapping[int, Bot]:
        return MappingProxyType(self._bots)

    def _register_bot(self, bot: Bot) -> None:
        self._bots[bot.info.id] = bot

    def _unregister_bot(self, bot: Bot) -> None:
        self._bots.pop(bot.info.id, None)

    async def _on_startup(
        self,
        app: AppT,
        *args: Any,
        bots: Iterable[Bot] | None = None,
        **kwargs: Any,
    ) -> None:
        all_bots = set(self.bots.values())

        if bots is not None:
            all_bots |= set(bots)

        webhook.info(
            "Starting multi-bot webhook engine with %s bot(s)",
            len(all_bots),
        )
        for bot in all_bots:
            lifecycle_data = self._build_lifecycle_data(app=app, bot=bot, **kwargs)
            self.dispatcher.workflow_data.update(lifecycle_data)

            await self.dispatcher.feed_signal(BeforeStartup(), bot)
            await bot.get_my_info()
            self._register_bot(bot)
            await self.dispatcher.feed_signal(AfterStartup(), bot)

    def _get_task_tracker(self, bot: Bot) -> TaskTracker:
        tracker = self._task_trackers.get(bot.info.id)

        if tracker is None:
            tracker = TaskTracker()
            self._task_trackers[bot.info.id] = tracker

        return tracker

    async def _on_shutdown(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        bots = tuple(self._bots.values())
        webhook.info(
            "Stopping %s with %s bot(s)",
            self.__class__.__name__,
            len(bots),
        )

        lifecycle_data = self._build_lifecycle_data(
            app=app,
            bots=set(bots),
            **kwargs,
        )
        self.dispatcher.workflow_data.update(lifecycle_data)
        await self.dispatcher.feed_signal(BeforeShutdown())

        for bot in bots:
            if (tracker := self._task_trackers.pop(bot.info.id, None)) is not None:
                await tracker.close(timeout=self.shutdown_timeout)
            self._unregister_bot(bot)
            await bot.close()

        await self.dispatcher.feed_signal(AfterShutdown())
