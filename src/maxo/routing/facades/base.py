from typing import Generic, TypeVar

from maxo.bot.bot import Bot
from maxo.routing.mixins import SubscriptionMethodsFacade
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class BaseUpdateFacade(SubscriptionMethodsFacade, Generic[_UpdateT]):
    __slots__ = ("_update",)

    def __init__(
        self,
        bot: Bot,
        update: _UpdateT,
    ) -> None:
        super().__init__(bot)
        self._update = update

    @property
    def update(self) -> _UpdateT:
        return self._update
