from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from adaptix.load_error import LoadError
from unihttp.serializers.adaptix.serialize import DEFAULT_RETORT

from maxo import Bot, Dispatcher
from maxo.loggers import webhook
from maxo.routing.signals import MaxoUpdate
from maxo.serialization import get_retort
from maxo.transport.webhook.configs.webhook import WebhookConfig
from maxo.transport.webhook.engines.errors import (
    BotNotFoundError,
    InvalidJsonError,
    RequestHandlingStoppedError,
)
from maxo.transport.webhook.errors import MaxoWebhookError
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security import Security
from maxo.transport.webhook.tasks import TaskTracker
from maxo.transport.webhook.web.base import WebAdapter, WebRequest
from maxo.types import Updates

AppT = TypeVar("AppT")
RawRequestT = TypeVar("RawRequestT")
FrameworkResponseT = TypeVar("FrameworkResponseT")


class BaseWebhookEngine(ABC, Generic[AppT, RawRequestT, FrameworkResponseT]):
    def __init__(
        self,
        dispatcher: Dispatcher,
        web: WebAdapter[AppT, RawRequestT, FrameworkResponseT],
        route: Route,
        security: Security | None = None,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self.dispatcher = dispatcher
        self.web = web
        self.route = route
        self.security = security

        self.shutdown_timeout = shutdown_timeout
        self._is_shutting_down = False

    def register(self, app: AppT) -> None:
        webhook.info(
            "Registering webhook path %s via %s",
            self.route.path,
            self.web.__class__.__name__,
        )
        if self.security is None:
            webhook.warning(
                "Webhook is registered without security: "
                "anyone who knows path %s can feed updates to the bot. "
                "Pass security=Security(secret=...) to the engine.",
                self.route.path,
            )
        self.web.register(
            app=app,
            path=self.route.path,
            handler=self.handle_request,
            on_startup=self.on_startup,
            on_shutdown=self.on_shutdown,
        )

    async def handle_request(
        self,
        request: WebRequest[RawRequestT],
    ) -> FrameworkResponseT:
        try:
            self._ensure_accepting_requests()

            route_params = await self.route.match(request)

            if self.security is not None:
                await self.security.verify(
                    request=request,
                    route_params=route_params,
                )

            bot = await self._resolve_bot(route_params=route_params)
            if bot is None:
                raise BotNotFoundError(route_param_names=route_params.keys())

            try:
                raw_update = await request.json()
            except ValueError as exc:
                raise InvalidJsonError(original_error=exc) from exc

            try:
                update = MaxoUpdate(update=get_retort().load(raw_update, Updates))
            except LoadError as exc:
                raise InvalidJsonError(original_error=exc) from exc

            webhook.debug("New update: %s", update.update)

            self._ensure_accepting_requests(bot)

            self._get_task_tracker(bot).spawn(  # type: ignore[unused-awaitable]
                self.dispatcher.feed_update(bot=bot, update=update),
            )
            return self.web.json_response(status_code=200, data={})

        except MaxoWebhookError as exc:
            webhook.log(
                exc.log_level,
                "Webhook request failed: %s: %s",
                exc.code,
                exc,
                extra={
                    "error_type": exc.__class__.__name__,
                    "status_code": exc.status_code,
                },
            )

            return self.web.json_response(
                status_code=exc.status_code,
                data=exc.response_payload(),
            )

    async def on_startup(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        await self._on_startup(app, *args, **kwargs)
        self._is_shutting_down = False

    async def on_shutdown(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        self._is_shutting_down = True
        await self._on_shutdown(app, *args, **kwargs)

    @abstractmethod
    async def _on_startup(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _on_shutdown(self, app: AppT, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _resolve_bot(self, route_params: RouteParams) -> Bot | None: ...

    @abstractmethod
    def _get_task_tracker(self, bot: Bot) -> TaskTracker:
        raise NotImplementedError

    def _build_lifecycle_data(self, *, app: AppT, **kwargs: Any) -> dict[str, Any]:
        return {
            "dispatcher": self.dispatcher,
            **self.dispatcher.workflow_data,
            "app": app,
            "webhook_engine": self,
            **kwargs,
        }

    async def _build_webhook_kwargs(
        self,
        bot: Bot,
        base_config: WebhookConfig,
        override_config: WebhookConfig | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = DEFAULT_RETORT.dump(base_config)
        if override_config is not None:
            kwargs.update(DEFAULT_RETORT.dump(override_config))
        if self.security is not None:
            secret = await self.security.secret(bot)
            if secret is not None:
                kwargs["secret"] = secret
        return kwargs

    def _ensure_accepting_requests(self, bot: Bot | None = None) -> None:
        if self._is_shutting_down or (bot is not None and bot.closed):
            raise RequestHandlingStoppedError
