from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.chat import Chat


class ChatList(MaxoType, BotMixin):
    """
    Args:
        chats: Список запрашиваемых чатов
        marker: Указатель на следующую страницу запрашиваемых чатов
    """

    chats: list[Chat]
    """Список запрашиваемых чатов"""

    marker: int | None = None
    """Указатель на следующую страницу запрашиваемых чатов"""

    @property
    def unsafe_marker(self) -> int:
        if is_defined(self.marker):
            return self.marker

        raise AttributeIsEmptyError(
            obj=self,
            attr="marker",
        )
