from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade


class MessageRemoved(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только сообщение будет удалено

    Args:
        chat_id: ID чата, где сообщение было удалено. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        message_id: ID удалённого сообщения
        post_id: Идентификатор поста в канале, к которому оставлен комментарий
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

    post_id: str | None = None
    """Идентификатор поста в канале, к которому оставлен комментарий"""

    @property
    def unsafe_post_id(self) -> str:
        if is_defined(self.post_id):
            return self.post_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="post_id",
        )
