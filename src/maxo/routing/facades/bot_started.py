from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.bot_started import BotStarted
from maxo.types.user import User


class BotStartedFacade(BaseUpdateFacade[BotStarted], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def payload(self) -> Omittable[str | None]:
        return self._update.payload

    @property
    def user_locale(self) -> Omittable[str]:
        return self._update.user_locale
