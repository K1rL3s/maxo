from enum import StrEnum


class ChatType(StrEnum):
    """Тип чата: диалог, чат"""

    CHANNEL = "channel"
    CHAT = "chat"
    DIALOG = "dialog"

    PRIVATE = DIALOG  # Подражание aiogram
    GROUP = CHAT  # Подражание aiogram
    SUPERGROUP = CHAT  # Подражание aiogram
