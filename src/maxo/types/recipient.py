from maxo.enums.chat_type import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxoType


class Recipient(MaxoType):
    """
    Новый получатель сообщения. Может быть пользователем, чатом или каналом

    Args:
        chat_id: ID чата или канала - в зависимости от ограничений метода и от того, с чем вы работаете. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)
        chat_type: Тип чата:
             - `chat` - групповой чат
             - `channel` - канал или комментарий к посту (для вызовов методов группы `/comments`)
             - `dialog` - диалог
        post_id: Идентификатор поста в канале, к которому оставлен комментарий
        user_id: ID получателя сообщения в диалоге (пользователя или бота). Если сообщение отправлено в групповой чат или канал, то параметр отсутствует
    """

    chat_type: ChatType
    """
    Тип чата:
         - `chat` - групповой чат
         - `channel` - канал или комментарий к посту (для вызовов методов группы `/comments`)
         - `dialog` - диалог
    """

    chat_id: int | None = None
    """ID чата или канала - в зависимости от ограничений метода и от того, с чем вы работаете. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)"""
    post_id: str | None = None
    """Идентификатор поста в канале, к которому оставлен комментарий"""
    user_id: int | None = None
    """ID получателя сообщения в диалоге (пользователя или бота). Если сообщение отправлено в групповой чат или канал, то параметр отсутствует"""

    @property
    def unsafe_chat_id(self) -> int:
        if is_defined(self.chat_id):
            return self.chat_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="chat_id",
        )

    @property
    def unsafe_post_id(self) -> str:
        if is_defined(self.post_id):
            return self.post_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="post_id",
        )

    @property
    def unsafe_user_id(self) -> int:
        if is_defined(self.user_id):
            return self.user_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_id",
        )
