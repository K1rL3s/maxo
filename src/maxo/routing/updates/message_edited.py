from maxo.enums.update_type import UpdateType
from maxo.routing.mixins import MessageMethodsFacade
from maxo.routing.updates.base import MaxUpdate
from maxo.types.message import Message


class MessageEdited(MaxUpdate, MessageMethodsFacade):
    """
    Вы получите это событие, как только пользователь отредактирует сообщение

    Args:
        message: Отредактированное сообщение
        type:
    """

    type = UpdateType.MESSAGE_EDITED

    message: Message
    """Отредактированное сообщение"""

    @property
    def text(self) -> str | None:
        return self.message.body.text
