from maxo.types.base import MaxoType
from maxo.types.message import Message


class MessageList(MaxoType):
    """
    Массив сообщений. Может быть как с пагинацией, так и без - если запрошены конкретные сообщения по их идентификаторам

    Args:
        messages: Массив сообщений
    """

    messages: list[Message]
    """Массив сообщений"""
