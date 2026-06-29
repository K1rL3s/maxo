from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.message_removed import MessageRemoved


class MessageRemovedFacade(BaseUpdateFacade[MessageRemoved], ChatMethodsFacade):
    @property
    def message_id(self) -> str:
        return self._update.message_id

    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user_id(self) -> int:
        return self._update.user_id
