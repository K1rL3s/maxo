from datetime import datetime
from typing import Self

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins import MessageMethodsFacade
from maxo.types.base import MaxoType
from maxo.types.linked_message import LinkedMessage
from maxo.types.message_body import MessageBody
from maxo.types.message_stat import MessageStat
from maxo.types.recipient import Recipient
from maxo.types.user import User
from maxo.utils.link import id_to_message_url


class Message(MaxoType, MessageMethodsFacade):
    """
    Содержит общую информацию о сообщении в чате или посте в канале: данные об отправителе и получателе, время создания сообщения, содержимое (текст и вложения), контекст связи с другими сообщениями (ответ или пересылка), а также публичную ссылку и статистику для постов в каналах

    Возвращается в ответ на вызовы методов группы [`/messages`](https://dev.max.ru/docs-api/methods/GET/messages) и [`/chats/{chatId}/pin`](https://dev.max.ru/docs-api/methods/PUT/chats/-chatId-/pin)

    Args:
        body: Содержимое сообщения. Текст + вложения. Может быть `null`, если сообщение содержит только пересланное сообщение
        link: Пересланное или ответное сообщение
        recipient: Получатель сообщения: пользователь или бот (для диалога), канал или чат
             **Обратите внимание**: все параметры в объекте относятся к получателю сообщения
        sender: Отправитель сообщения: пользователь или бот
            **Обратите внимание**:
            - Все параметры в объекте относятся к отправителю сообщения
            - Объект отсутствует, если сообщение отправлено в канал
        stat: Статистика просмотров постов - возвращается только для каналов
        timestamp: Время создания сообщения в формате Unix timestamp в миллисекундах
        url: Публичная ссылка на пост в канале. Отсутствует для диалогов и групповых чатов
    """

    body: MessageBody
    """Содержимое сообщения. Текст + вложения. Может быть `null`, если сообщение содержит только пересланное сообщение"""
    recipient: Recipient
    """
    Получатель сообщения: пользователь или бот (для диалога), канал или чат

     **Обратите внимание**: все параметры в объекте относятся к получателю сообщения
    """
    timestamp: datetime
    """Время создания сообщения в формате Unix timestamp в миллисекундах"""

    link: Omittable[LinkedMessage | None] = Omitted()
    """Пересланное или ответное сообщение"""
    sender: Omittable[User] = Omitted()
    """
    Отправитель сообщения: пользователь или бот

    **Обратите внимание**:
        - Все параметры в объекте относятся к отправителю сообщения
        - Объект отсутствует, если сообщение отправлено в канал
    """
    stat: Omittable[MessageStat | None] = Omitted()
    """Статистика просмотров постов - возвращается только для каналов"""
    url: Omittable[str | None] = Omitted()
    """Публичная ссылка на пост в канале. Отсутствует для диалогов и групповых чатов"""

    # Для MessageMethodsFacade
    @property
    def message(self) -> Self:
        return self

    @property
    def unsafe_link(self) -> LinkedMessage:
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

    @property
    def unsafe_stat(self) -> MessageStat:
        if is_defined(self.stat):
            return self.stat

        raise AttributeIsEmptyError(
            obj=self,
            attr="stat",
        )

    @property
    def unsafe_url(self) -> str:
        if is_defined(self.url):
            return self.url

        raise AttributeIsEmptyError(
            obj=self,
            attr="url",
        )

    @property
    def generated_url(self) -> str | None:
        """
        Генерирует ссылку на сообщение.

        Возвращает:
            str | None: Ссылка на сообщение или `None`, если `recipient.chat_id` не определен.
        """
        if not is_defined(self.recipient.chat_id):
            return None

        return id_to_message_url(
            sequence_id=self.body.seq,
            chat_id=self.recipient.chat_id,
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
