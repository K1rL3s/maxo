from typing import Any, Generic

from maxo import Bot, Dispatcher
from maxo.loggers import webhook
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook.configs.webhook import WebhookConfig
from maxo.transport.webhook.engines.base import (
    AppT,
    BaseWebhookEngine,
    FrameworkResponseT,
    RawRequestT,
)
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security import Security
from maxo.transport.webhook.tasks import TaskTracker
from maxo.transport.webhook.web.base import WebAdapter
from maxo.types import SimpleQueryResult


class SingleBotEngine(
    BaseWebhookEngine[AppT, RawRequestT, FrameworkResponseT],
    Generic[AppT, RawRequestT, FrameworkResponseT],
):
    def __init__(
        self,
        dispatcher: Dispatcher,
        bot: Bot,
        web: WebAdapter[AppT, RawRequestT, FrameworkResponseT],
        route: Route,
        security: Security | None = None,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self.bot = bot
        self._task_tracker = TaskTracker()

        super().__init__(
            dispatcher=dispatcher,
            web=web,
            route=route,
            security=security,
            shutdown_timeout=shutdown_timeout,
        )

    async def _resolve_bot(self, route_params: RouteParams) -> Bot:
        return self.bot

    def _get_task_tracker(self, bot: Bot) -> TaskTracker:
        return self._task_tracker

    async def subscribe(
        self,
        webhook_config: WebhookConfig | None = None,
    ) -> SimpleQueryResult:
        if not self.bot.started:  # for route.build_url
            await self.bot.get_my_info()

        kwargs = await self._build_webhook_kwargs(
            bot=self.bot,
            base_config=webhook_config or WebhookConfig(),
        )
        return await self.bot.subscribe(
            url=await self.route.build_url(bot=self.bot),
            **kwargs,
        )

    async def _on_startup(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        lifecycle_data = self._build_lifecycle_data(app=app, bot=self.bot, **kwargs)
        self.dispatcher.workflow_data.update(lifecycle_data)

        await self.dispatcher.feed_signal(BeforeStartup(), self.bot)
        if not self.bot.started:
            await self.bot.get_my_info()
        info = self.bot.info
        await self.dispatcher.feed_signal(AfterStartup(), self.bot)

        webhook.info("Starting single-bot webhook engine for bot %s", info.id)

    async def _on_shutdown(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        token = self.bot.token
        bot_id = self.bot.info.id if self.bot.started else f"{token[:6]}***{token[-4:]}"
        webhook.info(
            "Stopping single-bot webhook engine for bot %s",
            bot_id,
        )
        await self._task_tracker.close(timeout=self.shutdown_timeout)

        lifecycle_data = self._build_lifecycle_data(app=app, bot=self.bot, **kwargs)
        self.dispatcher.workflow_data.update(lifecycle_data)

        await self.dispatcher.feed_signal(BeforeShutdown(), self.bot)
        await self.bot.close()
        await self.dispatcher.feed_signal(AfterShutdown(), self.bot)
