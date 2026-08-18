from maxo.enums.chat_type import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxoType


class Recipient(MaxoType):
    """
    Новый получатель сообщения. Может быть пользователем или чатом

    Args:
        chat_id: ID чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        chat_type: Тип чата:
             - `chat` - групповой чат
             - `channel` - канал
             - `dialog` - диалог
        user_id: ID получателя сообщения в диалоге (пользователя или бота). Если сообщение отправлено в групповой чат или канал, то параметр отсутствует
    """

    chat_type: ChatType
    """
    Тип чата:
         - `chat` - групповой чат
         - `channel` - канал
         - `dialog` - диалог
    """

    chat_id: int | None = None
    """ID чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
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
    def unsafe_user_id(self) -> int:
        if is_defined(self.user_id):
            return self.user_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_id",
        )
