from typing import TypeAlias

from . import DialogCleared, DialogMuted, DialogRemoved, DialogUnmuted
from .bot_added_to_chat import BotAddedToChat
from .bot_removed_from_chat import BotRemovedFromChat
from .bot_started import BotStarted
from .bot_stopped import BotStopped
from .chat_title_changed import ChatTitleChanged
from .message_callback import MessageCallback
from .message_created import MessageCreated
from .message_edited import MessageEdited
from .message_removed import MessageRemoved
from .user_added_to_chat import UserAddedToChat
from .user_removed_from_chat import UserRemovedFromChat

Updates: TypeAlias = (
    BotAddedToChat
    | BotRemovedFromChat
    | BotStarted
    | BotStopped
    | ChatTitleChanged
    | DialogCleared
    | DialogMuted
    | DialogRemoved
    | DialogUnmuted
    | MessageCallback
    | MessageCreated
    | MessageEdited
    | MessageRemoved
    | UserAddedToChat
    | UserRemovedFromChat
)
