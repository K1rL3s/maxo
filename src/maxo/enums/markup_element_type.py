from enum import StrEnum


class MarkupElementType(StrEnum):
    EMPHASIZED = "emphasized"
    HEADING = "heading"
    HIGHLIGHTED = "highlighted"
    LINK = "link"
    MONOSPACED = "monospaced"
    QUOTE = "quote"
    STRIKETHROUGH = "strikethrough"
    STRONG = "strong"
    UNDERLINE = "underline"
    USER_MENTION = "user_mention"
