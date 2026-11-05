from typing import TypeAlias

from maxo.types.bot_added_to_chat import BotAddedToChat
from maxo.types.bot_admin_permissions_changed import BotAdminPermissionsChanged
from maxo.types.bot_removed_from_chat import BotRemovedFromChat
from maxo.types.bot_started import BotStarted
from maxo.types.bot_stopped import BotStopped
from maxo.types.chat_title_changed import ChatTitleChanged
from maxo.types.comment_created import CommentCreated
from maxo.types.comment_edited import CommentEdited
from maxo.types.comment_removed import CommentRemoved
from maxo.types.dialog_cleared import DialogCleared
from maxo.types.dialog_muted import DialogMuted
from maxo.types.dialog_removed import DialogRemoved
from maxo.types.dialog_unmuted import DialogUnmuted
from maxo.types.message_callback import MessageCallback
from maxo.types.message_created import MessageCreated
from maxo.types.message_edited import MessageEdited
from maxo.types.message_removed import MessageRemoved
from maxo.types.user_added_to_chat import UserAddedToChat
from maxo.types.user_removed_from_chat import UserRemovedFromChat

Updates: TypeAlias = (
    BotAddedToChat
    | BotAdminPermissionsChanged
    | BotRemovedFromChat
    | BotStarted
    | BotStopped
    | ChatTitleChanged
    | CommentCreated
    | CommentEdited
    | CommentRemoved
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
