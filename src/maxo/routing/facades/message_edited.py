from maxo.routing.facades.base import BaseUpdateFacade
from maxo.types.facades import MessageMethodsFacade
from maxo.types.message import Message
from maxo.types.message_edited import MessageEdited


class MessageEditedFacade(BaseUpdateFacade[MessageEdited], MessageMethodsFacade):
    @property
    def message(self) -> Message:
        return self._update.message

    @property
    def text(self) -> str | None:
        return self._update.text
