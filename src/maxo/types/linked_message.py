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
        chat_id: Чат или канал, в котором сообщение было изначально опубликовано. Только для пересланных сообщений с `type = forward`. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)
        message:
        sender: Пользователь или бот, отправивший сообщение
        type: Тип связанного сообщения:
            - `"reply"` - ответ на сообщение в чате
            - `"forward"` - пересланное сообщение в чате
    """

    message: MessageBody
    type: MessageLinkType
    """
    Тип связанного сообщения:
        - `"reply"` - ответ на сообщение в чате
        - `"forward"` - пересланное сообщение в чате
    """

    chat_id: Omittable[int] = Omitted()
    """Чат или канал, в котором сообщение было изначально опубликовано. Только для пересланных сообщений с `type = forward`. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)"""
    sender: Omittable[User | None] = Omitted()
    """Пользователь или бот, отправивший сообщение"""

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
            str | None: Ссылка на сообщение или `None`, если `chat_id` не определен
            или равен 0: так MAX отдаёт чат-источник, к которому у бота нет доступа.
        """
        if not is_defined(self.chat_id) or self.chat_id == 0:
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
