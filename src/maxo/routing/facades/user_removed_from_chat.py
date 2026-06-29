from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.user_removed_from_chat import UserRemovedFromChat
from maxo.types.user import User


class UserRemovedFromChatFacade(
    BaseUpdateFacade[UserRemovedFromChat],
    ChatMethodsFacade,
):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def admin_id(self) -> Omittable[int]:
        return self._update.admin_id

    @property
    def is_channel(self) -> bool:
        return self._update.is_channel
