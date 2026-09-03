from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.dialog_removed import DialogRemoved
from maxo.types.facades import ChatMethodsFacade
from maxo.types.user import User


class DialogRemovedFacade(BaseUpdateFacade[DialogRemoved], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def user_locale(self) -> Omittable[str]:
        return self._update.user_locale
