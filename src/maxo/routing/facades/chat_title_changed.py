from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.chat_title_changed import ChatTitleChanged
from maxo.types.user import User


class ChatTitleChangedFacade(BaseUpdateFacade[ChatTitleChanged], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def title(self) -> str:
        return self._update.title
