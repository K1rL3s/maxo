from maxo.enums.update_type import UpdateType
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.user import User


class ChatTitleChanged(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только будет изменено название чата

    Args:
        chat_id: ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        title: Новое название
        type:
        user: Пользователь, который изменил название
    """

    type = UpdateType.CHAT_TITLE_CHANGED

    chat_id: int
    """ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    title: str
    """Новое название"""
    user: User
    """Пользователь, который изменил название"""
