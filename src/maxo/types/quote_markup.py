from maxo.enums.markup_element_type import MarkupElementType
from maxo.types.markup_element import MarkupElement


class QuoteMarkup(MarkupElement):
    """
    Представляет цитату

    Args:
        type:
    """

    type: MarkupElementType = MarkupElementType.QUOTE
