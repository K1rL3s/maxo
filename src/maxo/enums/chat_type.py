from enum import StrEnum


class ChatType(StrEnum):
    CHANNEL = "channel"
    CHAT = "chat"
    DIALOG = "dialog"

    # Подражание aiogram
    PRIVATE = DIALOG
    GROUP = CHAT
    SUPERGROUP = CHAT
