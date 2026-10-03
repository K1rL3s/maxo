from enum import StrEnum


class ChatStatus(StrEnum):
    """Статус чата для текущего бота"""

    ACTIVE = "active"
    CLOSED = "closed"
    LEFT = "left"
    REMOVED = "removed"
    SUSPENDED = "suspended"
