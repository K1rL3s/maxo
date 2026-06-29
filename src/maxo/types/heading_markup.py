from maxo.enums.markup_element_type import MarkupElementType
from maxo.types.markup_element import MarkupElement


class HeadingMarkup(MarkupElement):
    """
    Представляет заголовок

    Args:
        type:
    """

    type: MarkupElementType = MarkupElementType.HEADING
