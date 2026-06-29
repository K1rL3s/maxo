from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.bot_removed_from_chat import BotRemovedFromChat
from maxo.types.user import User


class BotRemovedFromChatFacade(BaseUpdateFacade[BotRemovedFromChat], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def is_channel(self) -> bool:
        return self._update.is_channel
