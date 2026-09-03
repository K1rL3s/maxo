from datetime import datetime

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.comment_linked_message import CommentLinkedMessage
from maxo.types.comment_message_body import CommentMessageBody
from maxo.types.facades import CommentMethodsFacade
from maxo.types.message import Message
from maxo.types.recipient import Recipient
from maxo.types.user import User


class CommentMessage(Message, CommentMethodsFacade):
    """
    Комментарий в чате. Возвращается в ответ на запросы группы [`/comments`](https://dev.max.ru/docs-api/methods/GET/messages/-messageId-/comments). В отличие от обычного сообщения в чате или канале не содержит вложений `attachments` и не поддерживает пересылку комментариев (поле `link.type = forward`)

    Args:
        body: Информация о комментарии
        link: Комментарий, на который получен ответ
        recipient: Получатель сообщения: для комментариев - канал
        sender: Пользователь, отправивший комментарий. Может быть `null`, если сообщение было опубликовано от имени канала
        timestamp: Время создания сообщения в формате Unix timestamp в миллисекундах
    """

    body: CommentMessageBody  # type: ignore[mutable-override]
    """Информация о комментарии"""
    recipient: Recipient
    """Получатель сообщения: для комментариев - канал"""
    timestamp: datetime
    """Время создания сообщения в формате Unix timestamp в миллисекундах"""

    link: Omittable[CommentLinkedMessage | None] = Omitted()  # type: ignore[mutable-override]
    """Комментарий, на который получен ответ"""
    sender: Omittable[User | None] = Omitted()
    """Пользователь, отправивший комментарий. Может быть `null`, если сообщение было опубликовано от имени канала"""

    @property
    def unsafe_link(self) -> CommentLinkedMessage:
        if is_defined(self.link):
            return self.link

        raise AttributeIsEmptyError(
            obj=self,
            attr="link",
        )

    @property
    def unsafe_sender(self) -> User:
        if is_defined(self.sender):
            return self.sender

        raise AttributeIsEmptyError(
            obj=self,
            attr="sender",
        )
