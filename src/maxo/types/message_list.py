from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.message import Message


class MessageList(MaxoType, BotMixin):
    """
    Массив сообщений. Может быть как с пагинацией, так и без - если запрошены конкретные сообщения по их идентификаторам

    Args:
        messages: Массив сообщений
    """

    messages: list[Message]
    """Массив сообщений"""
