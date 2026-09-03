from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.message import Message


class GetPinnedMessageResult(MaxoType, BotMixin):
    """
    Args:
        message: Закреплённое сообщение. Может быть `null`, если в чате нет закреплённого сообщения
    """

    message: Omittable[Message | None] = Omitted()
    """Закреплённое сообщение. Может быть `null`, если в чате нет закреплённого сообщения"""

    @property
    def unsafe_message(self) -> Message:
        if is_defined(self.message):
            return self.message

        raise AttributeIsEmptyError(
            obj=self,
            attr="message",
        )
