import asyncio
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
    ) -> None:
        self.dispatcher = dispatcher
        self.web_adapter = web_adapter
        self.routing = routing
        self.security = security
        self.handle_in_background = handle_in_background
        self._background_feed_update_tasks: set[asyncio.Task[Any]] = set()

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
        bot = self._get_bot_from_request(bound_request)
        if bot is None:
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bot not found"},
            )

        if self.security is not None and not await self.security.verify(
            bot=bot,
            bound_request=bound_request,
        ):
            return self.web_adapter.create_json_response(
                status=403,
                payload={"detail": "Forbidden"},
            )

        try:
            raw_update = await bound_request.json()
        except JSONDecodeError:
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bad request"},
            )

        try:
            update = MaxoUpdate(update=bot.retort.load(raw_update, Updates))
        except LoadError:
            return self.web_adapter.create_json_response(
                status=400,
                payload={"detail": "Bad request"},
            )

        if self.handle_in_background:
            return await self._handle_request_background(bot=bot, update=update)
        return await self._handle_request(bot=bot, update=update)

    def register(self, app: Any) -> None:
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
        feed_update_task = asyncio.create_task(
            self._background_feed_update(bot=bot, update=update),
        )
        self._background_feed_update_tasks.add(feed_update_task)
        feed_update_task.add_done_callback(
            self._finalize_background_feed_update_task,
        )

        return self.web_adapter.create_json_response(status=200, payload={})

    def _finalize_background_feed_update_task(self, task: asyncio.Task[Any]) -> None:
        self._background_feed_update_tasks.discard(task)
        if task.cancelled():
            return

        exception = task.exception()
        if exception is not None:
            loggers.webhook.error(
                "Background update handling failed",
                exc_info=exception,
            )

    async def _drain_background_feed_update_tasks(self) -> None:
        """
        Дожидается завершения фоновых задач обработки апдейтов.

        Вызывается в `on_shutdown()` конкретных движков до закрытия бота,
        чтобы фоновые задачи не оставались брошенными при остановке.
        """
        while self._background_feed_update_tasks:
            tasks = tuple(self._background_feed_update_tasks)
            await asyncio.gather(*tasks, return_exceptions=True)
            self._background_feed_update_tasks.difference_update(tasks)
