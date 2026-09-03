from datetime import datetime

from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.dialog_muted import DialogMuted
from maxo.types.facades import ChatMethodsFacade
from maxo.types.user import User


class DialogMutedFacade(BaseUpdateFacade[DialogMuted], ChatMethodsFacade):
    @property
    def chat_id(self) -> int:
        return self._update.chat_id

    @property
    def user(self) -> User:
        return self._update.user

    @property
    def muted_until(self) -> datetime:
        return self._update.muted_until

    @property
    def user_locale(self) -> Omittable[str]:
        return self._update.user_locale
