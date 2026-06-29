from enum import StrEnum
from typing import TypeAlias


class TextFormat(StrEnum):
    """Формат текста сообщения"""

    HTML = "html"
    MARKDOWN = "markdown"


ParseMode: TypeAlias = TextFormat  # Подражание aiogram
