import asyncio
from collections.abc import MutableMapping
from typing import Any

from maxo import Bot, loggers
from maxo.fsm.key_builder import BaseKeyBuilder, DefaultKeyBuilder
from maxo.fsm.storages.base import BaseEventIsolation, BaseStorage
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.ctx import Ctx
from maxo.routing.facades.middleware import FacadeMiddleware
from maxo.routing.middlewares.error import ErrorMiddleware
from maxo.routing.middlewares.fsm_context import FSMContextMiddleware
from maxo.routing.middlewares.update_context import UpdateContextMiddleware
from maxo.routing.observers import UpdateObserver
from maxo.routing.routers.simple import Router
from maxo.routing.sentinels import UNHANDLED, SkipHandler
from maxo.routing.signals.base import BaseSignal
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.updates.base import BaseUpdate
from maxo.routing.utils._resolving_inner_middlewares import resolve_middlewares
from maxo.routing.utils.validate_router_graph import validate_router_graph


class Dispatcher(Router):
    update: UpdateObserver[MaxoUpdate[Any]]

    def __init__(
        self,
        *,
        workflow_data: MutableMapping[str, Any] | None = None,
        # State system settings
        storage: BaseStorage | None = None,
        events_isolation: BaseEventIsolation | None = None,
        key_builder: BaseKeyBuilder | None = None,
        disable_fsm: bool = False,
    ) -> None:
        super().__init__(self.__class__.__name__)

        self.workflow_data = workflow_data or {}
        self.workflow_data["dispatcher"] = self
        self.workflow_data["router"] = self
        self.workflow_data["dp"] = self

        self.update = self._observers[MaxoUpdate] = UpdateObserver[MaxoUpdate[Any]]()
        self.update.middleware.outer(ErrorMiddleware(self))
        self.update.middleware.outer(UpdateContextMiddleware())

        self.update.handler(self._feed_update_handler)

        # State system settings
        if not disable_fsm:
            if key_builder is None:
                key_builder = DefaultKeyBuilder()

            if storage is None:
                storage = MemoryStorage(key_builder=key_builder)

            if events_isolation is None:
                events_isolation = SimpleEventIsolation(key_builder=key_builder)

            # Note that when FSM middleware is disabled,
            # the event isolation is also disabled
            # Because the isolation mechanism is a part of the FS
            self.update.middleware.outer(
                FSMContextMiddleware(storage, events_isolation),
            )

        # Facade settings
        self.update.middleware.outer(FacadeMiddleware())

    async def feed_max_update(
        self,
        update: MaxoUpdate[Any],
        bot: Bot | None = None,
    ) -> Any:
        loop = asyncio.get_running_loop()
        start_time = loop.time()

        result = UNHANDLED
        try:
            result = await self.feed_update(update, bot)
        except Exception:  # noqa: BLE001
            duration = (loop.time() - start_time) * 1000
            loggers.dispatcher.exception(
                "%s update failed. Update type=%r marker=%r. Duration %d ms",
                "Handled" if result is not UNHANDLED else "Not handled",
                update.update.__class__.__name__,
                update.marker,
                duration,
            )
        else:
            duration = (loop.time() - start_time) * 1000
            loggers.dispatcher.info(
                "%s update: %r. Update type=%r marker=%r. Duration %d ms",
                "Handled" if result is not UNHANDLED else "Not handled",
                result,
                update.update.__class__.__name__,
                update.marker,
                duration,
            )
        return result

    async def feed_signal(self, signal: BaseSignal, bot: Bot | None = None) -> Any:
        return await self.feed_update(signal, bot)

    async def feed_update(self, update: BaseUpdate, bot: Bot | None = None) -> Any:
        ctx = Ctx({**self.workflow_data, "update": update})
        ctx["ctx"] = ctx

        if bot is not None:
            ctx["bot"] = bot
            ctx["bots"] = [bot]
            # Костыль для тестов (в них апдейты создаются без `.as_`)
            # и неправильных вызовах `.feed_update`. Удачи отдебажить >:)
            update.bot = bot

        return await self.trigger(ctx)

    async def _feed_update_handler(self, update: MaxoUpdate[Any], ctx: Ctx) -> Any:
        ctx_copy = Ctx(dict(ctx))
        ctx_copy["ctx"] = ctx_copy
        ctx_copy["update"] = update.update

        if "bot" in ctx:
            # Костыль для тестов (в них апдейты создаются без `.as_`)
            # и неправильных вызовах `.feed_update`. Удачи отдебажить >:)
            update.update.bot = update.bot = ctx["bot"]

        result = await self.trigger(ctx_copy)
        if result is UNHANDLED:
            raise SkipHandler

        return result

    async def _emit_before_startup_handler(self) -> None:
        validate_router_graph(self)
        resolve_middlewares(self)

        await super()._emit_before_startup_handler()
