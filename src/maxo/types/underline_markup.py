from maxo.enums.markup_element_type import MarkupElementType
from maxo.types.markup_element import MarkupElement


class UnderlineMarkup(MarkupElement):
    """
    Представляет <ins>подчёркнутый</ins> текст

    Args:
        type:
    """

    type: MarkupElementType = MarkupElementType.UNDERLINE
