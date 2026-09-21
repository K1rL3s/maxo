from maxo.enums.text_format import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.types.base import MaxoType
from maxo.types.new_message_link import NewMessageLink


class NewMessageBody(MaxoType):
    """
    Объект используется при отправке нового сообщения в чат или канал[`POST /messages`](https://dev.max.ru/docs-api/methods/POST/messages), редактировании существующего сообщения или поста [`PUT /messages`](https://dev.max.ru/docs-api/methods/PUT/messages), а также callback-отправке сообщения пользователю при нажатии им кнопки в чате или канале [`POST /answers`](https://dev.max.ru/docs-api/methods/POST/answers)

    Параметры объекта содержат: текст и способ его форматирования, вложения, ссылку на связанное сообщение (ответ или пересылка), настройку PUSH-уведомлений для участников чата

    Args:
        attachments: Вложения сообщения. Если поле пустое или равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены
        format: Разметка текста сообщения. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны
        notify: Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений
        text:
    """

    attachments: list[AttachmentsRequests | Attachments] | None = None
    """Вложения сообщения. Если поле пустое или равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены"""
    link: NewMessageLink | None = None
    """Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны"""
    text: str | None = None

    format: Omittable[TextFormat | None] = Omitted()
    """Разметка текста сообщения. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)"""
    notify: Omittable[bool] = Omitted()
    """Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений"""

    @property
    def unsafe_attachments(self) -> list[AttachmentsRequests | Attachments]:
        if is_defined(self.attachments):
            return self.attachments

        raise AttributeIsEmptyError(
            obj=self,
            attr="attachments",
        )

    @property
    def unsafe_format(self) -> TextFormat:
        if is_defined(self.format):
            return self.format

        raise AttributeIsEmptyError(
            obj=self,
            attr="format",
        )

    @property
    def unsafe_link(self) -> NewMessageLink:
        if is_defined(self.link):
            return self.link

        raise AttributeIsEmptyError(
            obj=self,
            attr="link",
        )

    @property
    def unsafe_notify(self) -> bool:
        if is_defined(self.notify):
            return self.notify

        raise AttributeIsEmptyError(
            obj=self,
            attr="notify",
        )

    @property
    def unsafe_text(self) -> str:
        if is_defined(self.text):
            return self.text

        raise AttributeIsEmptyError(
            obj=self,
            attr="text",
        )
