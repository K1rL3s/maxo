from typing import Any

from maxo import Bot, Dispatcher
from maxo.omit import Omittable, Omitted
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.routing.base import BaseRouting
from maxo.transport.webhook.security.security import Security


class SimpleEngine(WebhookEngine):
    """
    Simple webhook engine for single-bot applications.

    Uses a single Bot instance for all webhook requests.
    Ideal for applications that handle only one bot.
    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        bot: Bot,
        /,
        web_adapter: WebAdapter,
        routing: BaseRouting,
        security: Security | None = None,
        handle_in_background: bool = True,
    ) -> None:
        self.bot = bot
        super().__init__(
            dispatcher,
            web_adapter=web_adapter,
            routing=routing,
            security=security,
            handle_in_background=handle_in_background,
        )

    def _get_bot_from_request(self, bound_request: BoundRequest[Any]) -> Bot | None:
        """
        Return the single Bot instance for any request.

        :param bound_request: The incoming bound request.
        :return: The single Bot instance
        """
        return self.bot

    async def set_webhook(
        self,
        *,
        update_types: Omittable[list[str]] = Omitted(),
    ) -> Bot:
        """Set the webhook for the Bot instance."""
        secret_token: Omittable[str] = Omitted()
        if self.security is not None:
            secret_token = await self.security.get_secret_token(bot=self.bot)

        await self.bot.subscribe(
            url=self.routing.webhook_point(self.bot),
            secret=secret_token,
            update_types=update_types,
        )
        return self.bot

    async def on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        """Call on application startup. Emits dispatcher startup event."""
        workflow_data = self._build_workflow_data(app=app, bot=self.bot, **kwargs)
        self.dispatcher.workflow_data.update(workflow_data)

        await self.dispatcher.feed_signal(BeforeStartup(), self.bot)

        await self.bot.start()

        await self.dispatcher.feed_signal(AfterStartup(), self.bot)

    async def on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        """
        Call on application shutdown.

        Emits dispatcher shutdown event and closes bot session.
        """
        workflow_data = self._build_workflow_data(app=app, bot=self.bot, **kwargs)
        self.dispatcher.workflow_data.update(workflow_data)

        await self.dispatcher.feed_signal(BeforeShutdown(), self.bot)

        await self.bot.close()

        await self.dispatcher.feed_signal(AfterShutdown(), self.bot)
