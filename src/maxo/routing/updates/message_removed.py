from maxo.enums.update_type import UpdateType
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.base import MaxUpdate


class MessageRemoved(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только сообщение будет удалено

    Args:
        chat_id: ID чата, где сообщение было удалено. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        message_id: ID удалённого сообщения
        type:
        user_id: Пользователь, удаливший сообщение
    """

    type = UpdateType.MESSAGE_REMOVED

    chat_id: int
    """ID чата, где сообщение было удалено. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    message_id: str
    """ID удалённого сообщения"""
    user_id: int
    """Пользователь, удаливший сообщение"""
