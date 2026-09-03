from datetime import datetime
from typing import Any

from maxo.enums.chat_status import ChatStatus
from maxo.enums.chat_type import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.binding import BotMixin
from maxo.types.image import Image
from maxo.types.message import Message
from maxo.types.user_with_photo import UserWithPhoto


class Chat(MaxoType, BotMixin):
    """
    Объект содержит общую информацию о групповом чате или канале: его тип, настройки отображения (название, аватар, описание, ссылка), публичную доступность, а также информацию об участниках (владельце, боте и других пользователях), времени их последней активности и событиях

    Args:
        chat_id: ID чата или канала - в зависимости от ограничений метода и от того, с чем вы работаете. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        description: Описание чата или канала
        dialog_with_user: Данные о пользователе в диалоге (только для чатов типа `"dialog"`)
        icon: Аватар группового чата или канала
        is_public: Параметр показывает, доступен ли групповой чат или канал публично. Для диалогов и приватных каналов - всегда `false`
        last_event_time: Время последнего события в чате или канале в формате Unix timestamp в миллисекундах
        link: Ссылка на чат
        messages_count: Количество сообщений в групповом чате или постов канале
        owner_id: ID владельца чата или канала
        participants: Список участников в формате ключ-значение, где ключ - идентификатор участника `user_id`, а значение - время его последней активности в чате или канале `last_event_time`. Может быть `null`, если запрашивается список чатов
        participants_count: Количество участников чата или канала. Для диалогов всегда `2`
        pinned_message: Закреплённое сообщение в чате (возвращается только при запросе конкретного чата или канала)
        status: Статус чата:
            - `"active"` - Бот является активным участником чата
            - `"removed"` - Бот был удалён из чата
            - `"left"` - Бот покинул чат
            - `"closed"` - Чат был закрыт
        title: Отображаемое название чата или канала. Может быть `null` для диалогов
        type: Тип чата:
             - `"chat"` - Групповой чат
             - `"channel"` - Канал
             - `"dialog"` - Диалог
    """

    chat_id: int
    """ID чата или канала - в зависимости от ограничений метода и от того, с чем вы работаете. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    is_public: bool
    """Параметр показывает, доступен ли групповой чат или канал публично. Для диалогов и приватных каналов - всегда `false`"""
    last_event_time: datetime
    """Время последнего события в чате или канале в формате Unix timestamp в миллисекундах"""
    participants_count: int
    """Количество участников чата или канала. Для диалогов всегда `2`"""
    status: ChatStatus
    """
    Статус чата:
        - `"active"` - Бот является активным участником чата
        - `"removed"` - Бот был удалён из чата
        - `"left"` - Бот покинул чат
        - `"closed"` - Чат был закрыт
    """
    type: ChatType
    """
    Тип чата:
         - `"chat"` - Групповой чат
         - `"channel"` - Канал
         - `"dialog"` - Диалог
    """

    description: str | None = None
    """Описание чата или канала"""
    icon: Image | None = None
    """Аватар группового чата или канала"""
    title: str | None = None
    """Отображаемое название чата или канала. Может быть `null` для диалогов"""

    chat_message_id: Omittable[str | None] = Omitted()
    """Идентификатор сообщения с кнопкой, через которую был инициирован чата"""
    dialog_with_user: Omittable[UserWithPhoto | None] = Omitted()
    """Данные о пользователе в диалоге (только для чатов типа `"dialog"`)"""
    link: Omittable[str | None] = Omitted()
    """Ссылка на чат"""
    messages_count: Omittable[int | None] = Omitted()
    """Количество сообщений в групповом чате или постов канале"""
    owner_id: Omittable[int | None] = Omitted()
    """ID владельца чата или канала"""
    participants: Omittable[dict[str, Any] | None] = Omitted()
    """Список участников в формате ключ-значение, где ключ - идентификатор участника `user_id`, а значение - время его последней активности в чате или канале `last_event_time`. Может быть `null`, если запрашивается список чатов"""
    pinned_message: Omittable[Message | None] = Omitted()
    """Закреплённое сообщение в чате (возвращается только при запросе конкретного чата или канала)"""

    @property
    def id(self) -> int:
        return self.chat_id

    @property
    def unsafe_chat_message_id(self) -> str:
        if is_defined(self.chat_message_id):
            return self.chat_message_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="chat_message_id",
        )

    @property
    def unsafe_description(self) -> str:
        if is_defined(self.description):
            return self.description

        raise AttributeIsEmptyError(
            obj=self,
            attr="description",
        )

    @property
    def unsafe_dialog_with_user(self) -> UserWithPhoto:
        if is_defined(self.dialog_with_user):
            return self.dialog_with_user

        raise AttributeIsEmptyError(
            obj=self,
            attr="dialog_with_user",
        )

    @property
    def unsafe_icon(self) -> Image:
        if is_defined(self.icon):
            return self.icon

        raise AttributeIsEmptyError(
            obj=self,
            attr="icon",
        )

    @property
    def unsafe_link(self) -> str:
        if is_defined(self.link):
            return self.link

        raise AttributeIsEmptyError(
            obj=self,
            attr="link",
        )

    @property
    def unsafe_messages_count(self) -> int:
        if is_defined(self.messages_count):
            return self.messages_count

        raise AttributeIsEmptyError(
            obj=self,
            attr="messages_count",
        )

    @property
    def unsafe_owner_id(self) -> int:
        if is_defined(self.owner_id):
            return self.owner_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="owner_id",
        )

    @property
    def unsafe_participants(self) -> dict[str, Any]:
        if is_defined(self.participants):
            return self.participants

        raise AttributeIsEmptyError(
            obj=self,
            attr="participants",
        )

    @property
    def unsafe_pinned_message(self) -> Message:
        if is_defined(self.pinned_message):
            return self.pinned_message

        raise AttributeIsEmptyError(
            obj=self,
            attr="pinned_message",
        )

    @property
    def unsafe_title(self) -> str:
        if is_defined(self.title):
            return self.title

        raise AttributeIsEmptyError(
            obj=self,
            attr="title",
        )
