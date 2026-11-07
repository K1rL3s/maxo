from .bots.edit_bot_info import EditBotInfo  # type: ignore[deprecated]
from .bots.edit_my_commands import EditMyCommands
from .bots.get_my_info import GetMyInfo
from .chats.add_members import AddMembers  # type: ignore[deprecated]
from .chats.delete_admin import DeleteAdmin
from .chats.delete_admins import DeleteAdmins
from .chats.delete_chat import DeleteChat  # type: ignore[deprecated]
from .chats.edit_chat import EditChat
from .chats.get_admins import GetAdmins
from .chats.get_chat import GetChat
from .chats.get_chat_by_link import GetChatByLink  # type: ignore[deprecated]
from .chats.get_chats import GetChats  # type: ignore[deprecated]
from .chats.get_members import GetMembers
from .chats.get_membership import GetMembership
from .chats.get_pinned_message import GetPinnedMessage
from .chats.leave_chat import LeaveChat
from .chats.pin_message import PinMessage
from .chats.post_admins import PostAdmins
from .chats.remove_member import RemoveMember
from .chats.send_action import SendAction
from .chats.set_admins import SetAdmins
from .chats.unpin_message import UnpinMessage
from .comments.delete_comment import DeleteComment
from .comments.edit_comment import EditComment
from .comments.get_comment_by_id import GetCommentById
from .comments.get_comments import GetComments
from .comments.send_comment import SendComment
from .messages.answer_on_callback import AnswerOnCallback
from .messages.delete_message import DeleteMessage
from .messages.edit_message import EditMessage
from .messages.get_message_by_id import GetMessageById
from .messages.get_messages import GetMessages
from .messages.get_video_attachment_details import GetVideoAttachmentDetails
from .messages.send_message import SendMessage
from .subscriptions.get_subscriptions import GetSubscriptions
from .subscriptions.get_updates import GetUpdates
from .subscriptions.subscribe import Subscribe
from .subscriptions.unsubscribe import Unsubscribe
from .upload.get_upload_url import GetUploadUrl
from .upload.upload_media import UploadMedia

__all__ = (
    "AddMembers",
    "AnswerOnCallback",
    "DeleteAdmin",
    "DeleteAdmins",
    "DeleteChat",
    "DeleteComment",
    "DeleteMessage",
    "EditBotInfo",
    "EditChat",
    "EditComment",
    "EditMessage",
    "EditMyCommands",
    "GetAdmins",
    "GetChat",
    "GetChatByLink",
    "GetChats",
    "GetCommentById",
    "GetComments",
    "GetMembers",
    "GetMembership",
    "GetMessageById",
    "GetMessages",
    "GetMyInfo",
    "GetPinnedMessage",
    "GetSubscriptions",
    "GetUpdates",
    "GetUploadUrl",
    "GetVideoAttachmentDetails",
    "LeaveChat",
    "PinMessage",
    "PostAdmins",
    "RemoveMember",
    "SendAction",
    "SendComment",
    "SendMessage",
    "SetAdmins",
    "Subscribe",
    "UnpinMessage",
    "Unsubscribe",
    "UploadMedia",
)
