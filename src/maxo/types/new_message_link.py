from maxo.enums.message_link_type import MessageLinkType
from maxo.types.base import MaxoType


class NewMessageLink(MaxoType):
    """
    Args:
        mid: ID исходного сообщения
        type: Тип связанного сообщения:
             - `"forward"` - пересланное сообщение
             - `"reply"` - ответ на сообщение
    """

    mid: str
    """ID исходного сообщения"""
    type: MessageLinkType
    """
    Тип связанного сообщения:
         - `"forward"` - пересланное сообщение
         - `"reply"` - ответ на сообщение
    """
