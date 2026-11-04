from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Any

from adaptix.load_error import LoadError

from maxo import Bot, Dispatcher, loggers
from maxo.bot.methods.base import MaxoMethod
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.routing.base import BaseRouting
from maxo.transport.webhook.security.security import Security
from maxo.transport.webhook.tasks import TaskTracker
from maxo.types import Updates


class WebhookEngine(ABC):
    """
    Base webhook engine for processing Telegram bot updates.

    Handles incoming webhook requests, bot resolution, security checks,
    routing, and dispatching updates to the maxo dispatcher. Supports
    both synchronous and background processing.
    """

    def __init__(
        self,
        dispatcher: Dispatcher,
        /,
        web_adapter: WebAdapter,
        routing: BaseRouting,
        security: Security | None = None,
        handle_in_background: bool = True,
        shutdown_timeout: float = 10.0,
    ) -> None:
        self.dispatcher = dispatcher
        self.web_adapter = web_adapter
        self.routing = routing
        self.security = security
        self.handle_in_background = handle_in_background
        self.shutdown_timeout = shutdown_timeout
        self._is_shutting_down = False
        self._task_tracker = TaskTracker()

    @abstractmethod
    def _get_bot_from_request(self, bound_request: BoundRequest[Any]) -> Bot | None:
        raise NotImplementedError

    @abstractmethod
    async def set_webhook(self, *args: Any, **kwargs: Any) -> Bot:
        raise NotImplementedError

    @abstractmethod
    async def on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    def _build_workflow_data(self, app: Any, **kwargs: Any) -> dict[str, Any]:
        """Build workflow data for startup/shutdown events."""
        return {
            "app": app,
            "webhook_engine": self,
            **self.dispatcher.workflow_data,
            **kwargs,
        }

    async def handle_request(self, bound_request: BoundRequest[Any]) -> Any:
        if self._is_shutting_down:
            return self._shutting_down_response()

        bot = self._get_bot_from_request(bound_request)
        if bot is None:
            loggers.webhook.warning(
                "Вебхук %s: бот для запроса не найден",
                self.routing.path,
            )
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bot not found"},
            )

        if self.security is not None and not await self.security.verify(
            bot=bot,
            bound_request=bound_request,
        ):
            loggers.webhook.warning(
                "Вебхук %s: запрос отклонён проверкой безопасности",
                self.routing.path,
            )
            return self.web_adapter.create_json_response(
                status=403,
                payload={"detail": "Forbidden"},
            )

        try:
            raw_update = await bound_request.json()
        except JSONDecodeError:
            loggers.webhook.warning(
                "Вебхук %s: тело запроса не является корректным JSON",
                self.routing.path,
            )
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bad request"},
            )

        try:
            update = MaxoUpdate(update=bot.retort.load(raw_update, Updates))
        except LoadError:
            loggers.webhook.warning(
                "Вебхук %s: не удалось разобрать обновление",
                self.routing.path,
                exc_info=True,
            )
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bad request"},
            )

        loggers.webhook.debug("New update: %s", update.update)

        if self.handle_in_background:
            return await self._handle_request_background(bot=bot, update=update)
        return await self._handle_request(bot=bot, update=update)

    def register(self, app: Any) -> None:
        loggers.webhook.info(
            "Регистрация вебхука на пути %s через %s",
            self.routing.path,
            type(self.web_adapter).__name__,
        )
        if self.security is None:
            loggers.webhook.warning(
                "Вебхук на пути %s зарегистрирован без проверки безопасности: "
                "любой, кто знает путь, может отправлять боту обновления. "
                "Передайте security=Security(...) в engine",
                self.routing.path,
            )
        self.web_adapter.register(
            app=app,
            path=self.routing.path,
            handler=self.handle_request,
            on_startup=self.on_startup,
            on_shutdown=self.on_shutdown,
        )

    async def _handle_request(
        self,
        bot: Bot,
        update: MaxoUpdate[Any],
    ) -> Any:
        if self._is_shutting_down:
            return self._shutting_down_response()

        result = await self.dispatcher.feed_max_update(bot=bot, update=update)

        if not isinstance(result, MaxoMethod):
            return self.web_adapter.create_json_response(status=200, payload={})

        await bot.silent_call_method(method=result)
        return self.web_adapter.create_json_response(status=200, payload={})

    async def _background_feed_update(self, bot: Bot, update: MaxoUpdate[Any]) -> None:
        result = await self.dispatcher.feed_max_update(
            bot=bot,
            update=update,
        )  # **self.data
        if isinstance(result, MaxoMethod):
            await bot.silent_call_method(method=result)

    async def _handle_request_background(
        self,
        bot: Bot,
        update: MaxoUpdate[Any],
    ) -> Any:
        if self._is_shutting_down:
            return self._shutting_down_response()

        self._task_tracker.spawn(self._background_feed_update(bot=bot, update=update))
        return self.web_adapter.create_json_response(status=200, payload={})

    def _shutting_down_response(self) -> Any:
        loggers.webhook.debug(
            "Вебхук %s: идёт остановка, запрос отклонён",
            self.routing.path,
        )
        return self.web_adapter.create_json_response(
            status=503,
            payload={"detail": "Service unavailable"},
        )

    async def _stop_background_tasks(self) -> None:
        self._is_shutting_down = True
        await self._task_tracker.close(timeout=self.shutdown_timeout)
