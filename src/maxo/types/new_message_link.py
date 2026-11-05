from maxo.enums.message_link_type import MessageLinkType
from maxo.types.base import MaxoType


class NewMessageLink(MaxoType):
    """
    Args:
        mid: ID исходного сообщения
        type: Тип связанного сообщения:
            - `"reply"` - ответ на сообщение или комментарий в чате или канале
            - `"forward"` - пересланное сообщение в чате или канале
            **Для комментариев поддерживается только тип `reply`**
    """

    mid: str
    """ID исходного сообщения"""
    type: MessageLinkType
    """
    Тип связанного сообщения:
        - `"reply"` - ответ на сообщение или комментарий в чате или канале
        - `"forward"` - пересланное сообщение в чате или канале

    **Для комментариев поддерживается только тип `reply`**
    """
