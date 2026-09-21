from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.markup_elements import MarkupElements
from maxo.types.message_body import MessageBody


class CommentMessageBody(MessageBody):
    """
    Информация о комментарии

    Args:
        markup: Разметка текста комментария. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
            **Обратите внимание**: в тексте комментариев не поддерживаются гиперссылки и упоминание пользователя
        mid: Уникальный ID комментария
        seq: Порядковый номер расположения комментария в посте
        text: Текст комментария
    """

    mid: str
    """Уникальный ID комментария"""
    seq: int
    """Порядковый номер расположения комментария в посте"""

    text: str | None = None
    """Текст комментария"""

    markup: Omittable[list[MarkupElements] | None] = Omitted()
    """
    Разметка текста комментария. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)

    **Обратите внимание**: в тексте комментариев не поддерживаются гиперссылки и упоминание пользователя
    """

    @property
    def unsafe_markup(self) -> list[MarkupElements]:
        if is_defined(self.markup):
            return self.markup

        raise AttributeIsEmptyError(
            obj=self,
            attr="markup",
        )

    @property
    def unsafe_text(self) -> str:
        if is_defined(self.text):
            return self.text

        raise AttributeIsEmptyError(
            obj=self,
            attr="text",
        )
