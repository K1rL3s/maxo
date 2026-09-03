from maxo.enums.update_type import UpdateType
from maxo.types.base import MaxUpdate
from maxo.types.facades import ChatMethodsFacade
from maxo.types.user import User


class BotRemovedFromChat(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только бот будет удалён из чата

    Args:
        chat_id: ID чата, откуда был удалён бот. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        is_channel: Указывает, что бот удалён из канала, а не из чата
        type:
        user: Пользователь, удаливший бота из чата
    """

    type = UpdateType.BOT_REMOVED

    chat_id: int
    """ID чата, откуда был удалён бот. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    is_channel: bool
    """Указывает, что бот удалён из канала, а не из чата"""
    user: User
    """Пользователь, удаливший бота из чата"""
