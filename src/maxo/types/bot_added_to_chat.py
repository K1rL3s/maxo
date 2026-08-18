from maxo.enums.update_type import UpdateType
from maxo.routing.mixins import ChatMethodsFacade
from maxo.types.base import MaxUpdate
from maxo.types.user import User


class BotAddedToChat(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только бот будет добавлен в чат или канал

    Args:
        chat_id: ID чата или канала, куда был добавлен бот. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        is_channel: Указывает, что бот добавлен в канал, а не в чат
        type:
        user: Пользователь, добавивший бота в чат
    """

    type = UpdateType.BOT_ADDED

    chat_id: int
    """ID чата или канала, куда был добавлен бот. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    is_channel: bool
    """Указывает, что бот добавлен в канал, а не в чат"""
    user: User
    """Пользователь, добавивший бота в чат"""
