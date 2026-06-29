import asyncio
from asyncio import Task
from contextvars import copy_context
from typing import Any

from maxo import Bot, Dispatcher
from maxo.dialogs.api.entities import DialogUpdateEvent
from maxo.routing.signals import MaxoUpdate


class Updater:
    def __init__(self, dp: Dispatcher) -> None:
        if not isinstance(dp, Dispatcher):
            raise TypeError("Root router must be Dispatcher.")
        self.dp = dp

    async def notify(self, bot: Bot, update: DialogUpdateEvent) -> None:
        asyncio.get_running_loop().call_soon(
            self.notify_task,
            bot,
            update,
            context=copy_context(),
        )

    def notify_task(self, bot: Bot, update: DialogUpdateEvent) -> Task[Any]:
        return asyncio.create_task(self._process_update(bot, update))

    async def _process_update(self, bot: Bot, update: DialogUpdateEvent) -> None:
        await self.dp.feed_update(MaxoUpdate(update=update), bot)
