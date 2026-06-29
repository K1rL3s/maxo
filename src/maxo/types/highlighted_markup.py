from maxo.enums.markup_element_type import MarkupElementType
from maxo.types.markup_element import MarkupElement


class HighlightedMarkup(MarkupElement):
    """
    Представляет выделенный текст

    Args:
        type:
    """

    type: MarkupElementType = MarkupElementType.HIGHLIGHTED
