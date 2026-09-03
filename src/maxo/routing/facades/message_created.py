from maxo.omit import Omittable
from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.facades import MessageMethodsFacade
from maxo.types.message import Message
from maxo.types.message_created import MessageCreated


class MessageCreatedFacade(BaseUpdateFacade[MessageCreated], MessageMethodsFacade):
    @property
    def message(self) -> Message:
        return self._update.message

    @property
    def text(self) -> str | None:
        return self._update.text

    @property
    def user_locale(self) -> Omittable[str | None]:
        return self._update.user_locale
