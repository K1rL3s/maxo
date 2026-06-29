from maxo.enums.chat_type import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxoType


class Recipient(MaxoType):
    """
    Новый получатель сообщения. Может быть пользователем или чатом

    Args:
        chat_id: ID чата. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        chat_type: Тип чата
        user_id: ID пользователя, если сообщение было отправлено пользователю
    """

    chat_type: ChatType
    """Тип чата"""

    chat_id: int | None = None
    """ID чата. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    user_id: int | None = None
    """ID пользователя, если сообщение было отправлено пользователю"""

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
