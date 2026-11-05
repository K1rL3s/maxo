from maxo.enums.text_format import TextFormat
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.new_message_link import NewMessageLink


class NewCommentBody(MaxoType):
    """
    Объект используется при отправке нового комментария к посту в канале [`POST messages/-messageId-/comments`](https://dev.max.ru/docs-api/methods/POST/messages/-messageId-/comments) или редактировании старого [`PUT messages/-messageId-/comments`](https://dev.max.ru/docs-api/methods/PUT/messages/-messageId-/comments). В отличие от обычных сообщений в чатах и постов в каналах (объект [`NewMessageBody`](https://dev.max.ru/docs-api/objects/NewMessageBody)), в комментариях не поддерживаются вложения `attachments` и пересылка сообщения (тип `forward`)

    Args:
        format: Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на комментарий
        text: Текст комментария
    """

    link: NewMessageLink | None = None
    """Ссылка на комментарий"""
    text: str | None = None
    """Текст комментария"""

    format: Omittable[TextFormat | None] = Omitted()
    """Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)"""

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
    def unsafe_text(self) -> str:
        if is_defined(self.text):
            return self.text

        raise AttributeIsEmptyError(
            obj=self,
            attr="text",
        )
