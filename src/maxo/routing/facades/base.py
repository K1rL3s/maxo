from typing import Generic, TypeVar

from maxo.bot.bot import Bot
from maxo.types.base import BaseUpdate
from maxo.types.facades import SubscriptionMethodsFacade

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
