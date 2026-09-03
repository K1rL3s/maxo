from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.message import Message


class SendMessageResult(MaxoType, BotMixin):
    """
    Args:
        message:
    """

    message: Message
