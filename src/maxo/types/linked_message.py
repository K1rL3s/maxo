from maxo.enums.message_link_type import MessageLinkType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.message_body import MessageBody
from maxo.types.user import User
from maxo.utils.link import id_to_message_url


class LinkedMessage(MaxoType):
    """
    Args:
        chat_id: Чат, в котором сообщение было изначально опубликовано. Только для пересланных сообщений. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        message:
        sender: Пользователь, отправивший сообщение.
        type: Тип связанного сообщения
    """

    message: MessageBody
    type: MessageLinkType
    """Тип связанного сообщения"""

    chat_id: Omittable[int] = Omitted()
    """Чат, в котором сообщение было изначально опубликовано. Только для пересланных сообщений. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    sender: Omittable[User] = Omitted()
    """Пользователь, отправивший сообщение."""

    @property
    def unsafe_chat_id(self) -> int:
        if is_defined(self.chat_id):
            return self.chat_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="chat_id",
        )

    @property
    def unsafe_sender(self) -> User:
        if is_defined(self.sender):
            return self.sender

        raise AttributeIsEmptyError(
            obj=self,
            attr="sender",
        )

    @property
    def generated_url(self) -> str | None:
        """
        Генерирует ссылку на сообщение.

        Возвращает:
            str | None: Ссылка на сообщение или `None`, если `chat_id` не определен.
        """
        if not is_defined(self.chat_id):
            return None

        return id_to_message_url(
            sequence_id=self.message.seq,
            chat_id=self.chat_id,
        )

    @property
    def unsafe_generated_url(self) -> str:
        """
        Генерирует ссылку на сообщение.

        Если `generated_url` не определен, вызывает :py:exc:`~maxo.errors.AttributeIsEmptyError`.

        Возвращает:
            str: Ссылка на сообщение.
        """
        if is_defined(self.generated_url):
            return self.generated_url

        raise AttributeIsEmptyError(
            obj=self,
            attr="generated_url",
        )
