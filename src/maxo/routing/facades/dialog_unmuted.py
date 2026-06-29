from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.dialog_unmuted import DialogUnmuted
from maxo.types.user import User


class DialogUnmutedFacade(BaseUpdateFacade[DialogUnmuted], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def user_locale(self) -> Omittable[str]:
        return self._update.user_locale
