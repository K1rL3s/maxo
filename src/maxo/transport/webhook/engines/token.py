from typing import Any, cast

from maxo import Bot, Dispatcher
from maxo.omit import Omittable, Omitted
from maxo.routing.signals import (
    AfterShutdown,
    AfterStartup,
    BeforeShutdown,
    BeforeStartup,
)
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.config.bot import BotConfig
from maxo.transport.webhook.engines.base import WebhookEngine
from maxo.transport.webhook.routing.base import TokenRouting
from maxo.transport.webhook.security.security import Security


class TokenEngine(WebhookEngine):
    """
    Multi-bot webhook engine with dynamic bot resolution.

    Resolves Bot instances from request tokens. Creates and caches Bot
    instances on-demand. Suitable for multi-tenant applications.

    В отличие от Telegram, токен бота MAX не содержит идентификатор бота, а
    получить его можно только после старта бота (`get_my_info`). Поэтому боты
    кешируются по строке токена.
    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        /,
        web_adapter: WebAdapter,
        routing: TokenRouting,
        security: Security | None = None,
        bot_config: BotConfig | None = None,
        handle_in_background: bool = True,
    ) -> None:
        super().__init__(
            dispatcher,
            web_adapter=web_adapter,
            routing=routing,
            security=security,
            handle_in_background=handle_in_background,
        )
        self.bot_config = bot_config or BotConfig()
        self._bots: dict[str, Bot] = {}

    @property
    def token_routing(self) -> TokenRouting:
        # Базовый движок хранит `routing` как `BaseRouting`, но `TokenEngine`
        # всегда получает `TokenRouting` через конструктор, поэтому сужение
        # типа здесь безопасно.
        return cast(TokenRouting, self.routing)

    def _get_bot_from_request(self, bound_request: BoundRequest[Any]) -> Bot | None:
        """
        Get a :class:`Bot` instance from request by token.

        If the bot is not yet created, it will be created automatically.

        :param bound_request: Incoming request.
        :return: Bot instance or None.
        """
        token = self.token_routing.extract_token(bound_request)
        if not token:
            return None
        return self.get_bot(token)

    def get_bot(self, token: str) -> Bot:
        """
        Resolve or create a Bot instance by token and cache it.

        :param token: The bot token.
        :return: Bot instance.
        """
        bot = self._bots.get(token)
        if bot is None:
            bot = Bot(token=token, defaults=self.bot_config.defaults)
            self._bots[token] = bot
        return bot

    async def set_webhook(
        self,
        token: str,
        *,
        update_types: Omittable[list[str]] = Omitted(),
    ) -> Bot:
        """Set the webhook for the Bot instance resolved by token."""
        bot = self.get_bot(token)

        secret_token: Omittable[str] = Omitted()
        if self.security is not None:
            secret_token = await self.security.get_secret_token(bot=bot)

        await bot.subscribe(
            url=self.routing.webhook_point(bot),
            secret=secret_token,
            update_types=update_types,
        )
        return bot

    async def on_startup(
        self,
        app: Any,
        *args: Any,
        bots: set[Bot] | None = None,
        **kwargs: Any,
    ) -> None:
        """Call on application startup. Emits dispatcher startup event."""
        for bot in bots or ():
            self._bots.setdefault(bot.token, bot)
        all_bots = list(self._bots.values())

        workflow_data = self._build_workflow_data(app=app, bots=all_bots, **kwargs)
        self.dispatcher.workflow_data.update(workflow_data)

        await self.dispatcher.feed_signal(BeforeStartup())

        for bot in all_bots:
            await bot.start()

        await self.dispatcher.feed_signal(AfterStartup())

    async def on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        """
        Call on application shutdown.

        Emits dispatcher shutdown event and closes all bot sessions.
        """
        all_bots = list(self._bots.values())

        workflow_data = self._build_workflow_data(app=app, bots=all_bots, **kwargs)
        self.dispatcher.workflow_data.update(workflow_data)

        await self.dispatcher.feed_signal(BeforeShutdown())

        for bot in all_bots:
            await bot.close()

        await self.dispatcher.feed_signal(AfterShutdown())

        self._bots.clear()
