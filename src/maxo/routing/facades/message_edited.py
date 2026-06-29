from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.mixins import MessageMethodsFacade
from maxo.routing.updates.message_edited import MessageEdited
from maxo.types.message import Message


class MessageEditedFacade(BaseUpdateFacade[MessageEdited], MessageMethodsFacade):
    @property
    def message(self) -> Message:
        return self._update.message

    @property
    def text(self) -> str | None:
        return self._update.text
