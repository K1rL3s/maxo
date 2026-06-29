from typing import TYPE_CHECKING

from maxo.omit import Omittable, Omitted
from maxo.routing.mixins.bot import BotMethodsFacade
from maxo.types.get_subscriptions_result import GetSubscriptionsResult
from maxo.types.simple_query_result import SimpleQueryResult

if TYPE_CHECKING:
    from maxo.types.update_list import UpdateList


class SubscriptionMethodsFacade(BotMethodsFacade):
    __slots__ = ()

    async def get_subscriptions(self) -> GetSubscriptionsResult:
        return await self.bot.get_subscriptions()

    async def get_updates(
        self,
        limit: Omittable[int] = Omitted(),
        marker: Omittable[int | None] = Omitted(),
        timeout: Omittable[int] = Omitted(),
        types: Omittable[list[str] | None] = Omitted(),
    ) -> "UpdateList":
        return await self.bot.get_updates(
            limit=limit,
            marker=marker,
            timeout=timeout,
            types=types,
        )

    async def subscribe(
        self,
        url: str,
        secret: Omittable[str] = Omitted(),
        update_types: Omittable[list[str]] = Omitted(),
    ) -> SimpleQueryResult:
        return await self.bot.subscribe(
            url=url,
            secret=secret,
            update_types=update_types,
        )

    async def unsubscribe(self, url: str) -> SimpleQueryResult:
        return await self.bot.unsubscribe(url=url)
