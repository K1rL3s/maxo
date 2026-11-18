from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.user import User


class BotAddedToChat(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только бот будет добавлен в чат или канал

    Args:
        chat_id: ID чата или канала, куда был добавлен бот. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)
        is_channel: Указывает, что бот добавлен в канал, а не в чат
        type:
        user: Пользователь, добавивший бота в чат. С ноября 2026 года поле встречается только в старых событиях
    """

    type = UpdateType.BOT_ADDED

    chat_id: int
    """ID чата или канала, куда был добавлен бот. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)"""
    is_channel: bool
    """Указывает, что бот добавлен в канал, а не в чат"""

    user: Omittable[User] = Omitted()
    """Пользователь, добавивший бота в чат. С ноября 2026 года поле встречается только в старых событиях"""

    @property
    def unsafe_user(self) -> User:
        if is_defined(self.user):
            return self.user

        raise AttributeIsEmptyError(
            obj=self,
            attr="user",
        )
