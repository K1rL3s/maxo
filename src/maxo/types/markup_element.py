from maxo.enums.markup_element_type import MarkupElementType
from maxo.types.base import MaxoType


class MarkupElement(MaxoType):
    """
    Args:
        from_: Индекс начала элемента разметки в тексте. Нумерация с нуля
        length: Длина элемента разметки
        type: Тип элемента разметки. Может быть **жирный**,  *курсив*, ~зачеркнутый~, <ins>подчеркнутый</ins>, `моноширинный`, выделенный, цитата, заголовок, ссылка или упоминание пользователя
    """

    from_: int
    """Индекс начала элемента разметки в тексте. Нумерация с нуля"""
    length: int
    """Длина элемента разметки"""
    type: MarkupElementType
    """Тип элемента разметки. Может быть **жирный**,  *курсив*, ~зачеркнутый~, <ins>подчеркнутый</ins>, `моноширинный`, выделенный, цитата, заголовок, ссылка или упоминание пользователя"""

    @property
    def offset(self) -> int:
        # Подражание aiogram
        return self.from_
