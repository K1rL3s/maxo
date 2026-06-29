from maxo.enums.text_format import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.types.base import MaxoType
from maxo.types.new_message_link import NewMessageLink


class NewMessageBody(MaxoType):
    """
    Args:
        attachments: Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если пусто, все вложения будут удалены
        format: Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)
        link: Ссылка на сообщение
        notify: Если false, участники чата не будут уведомлены (по умолчанию `true`)
        text: Новый текст сообщения
    """

    attachments: list[AttachmentsRequests | Attachments] | None = None
    """Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если пусто, все вложения будут удалены"""
    link: NewMessageLink | None = None
    """Ссылка на сообщение"""
    text: str | None = None
    """Новый текст сообщения"""

    format: Omittable[TextFormat | None] = Omitted()
    """Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)"""
    notify: Omittable[bool] = Omitted()
    """Если false, участники чата не будут уведомлены (по умолчанию `true`)"""

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
