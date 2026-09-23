from maxo.enums.message_link_type import MessageLinkType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.comment_message_body import CommentMessageBody
from maxo.types.linked_message import LinkedMessage
from maxo.types.user import User


class CommentLinkedMessage(LinkedMessage):
    """
    Args:
        chat_id: Чат или канал, в котором сообщение было изначально опубликовано. Только для пересланных сообщений с `type = forward`. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)
        message:
        sender: Пользователь или бот, отправивший комментарий
        type: Тип связанного сообщения:
            - `"reply"` - ответ на сообщение или комментарий в чате или канале
            - `"forward"` - пересланное сообщение в чате или канале
            **Для комментариев поддерживается только тип `reply`**
    """

    message: CommentMessageBody  # type: ignore[mutable-override]
    type: MessageLinkType
    """
    Тип связанного сообщения:
        - `"reply"` - ответ на сообщение или комментарий в чате или канале
        - `"forward"` - пересланное сообщение в чате или канале

    **Для комментариев поддерживается только тип `reply`**
    """

    chat_id: Omittable[int] = Omitted()
    """Чат или канал, в котором сообщение было изначально опубликовано. Только для пересланных сообщений с `type = forward`. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)"""
    sender: Omittable[User | None] = Omitted()
    """Пользователь или бот, отправивший комментарий"""

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
