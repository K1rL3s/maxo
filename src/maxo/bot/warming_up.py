from enum import Enum
from typing import Any, TypeVar, assert_never

from adaptix import Retort

from maxo.bot.methods import (  # type: ignore[deprecated]
    AddMembers,
    AnswerOnCallback,
    DeleteAdmins,
    DeleteChat,
    DeleteComment,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditComment,
    EditMessage,
    EditMyCommands,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
    GetCommentById,
    GetComments,
    GetMembers,
    GetMembership,
    GetMessageById,
    GetMessages,
    GetMyInfo,
    GetPinnedMessage,
    GetSubscriptions,
    GetUpdates,
    GetUploadUrl,
    GetVideoAttachmentDetails,
    LeaveChat,
    PinMessage,
    PostAdmins,
    RemoveMember,
    SendAction,
    SendComment,
    SendMessage,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.bot.methods.base import MaxoMethod
from maxo.types import Updates


class WarmingUpType(Enum):
    METHOD = "method"
    TYPES = "types"


_METHOD_ROOTS: tuple[type[MaxoMethod[Any]], ...] = (
    AddMembers,
    AnswerOnCallback,
    DeleteAdmins,
    DeleteChat,
    DeleteComment,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditComment,
    EditMessage,
    EditMyCommands,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
    GetCommentById,
    GetComments,
    GetMembers,
    GetMembership,
    GetMessageById,
    GetMessages,
    GetMyInfo,
    GetPinnedMessage,
    GetSubscriptions,
    GetUpdates,
    GetUploadUrl,
    GetVideoAttachmentDetails,
    LeaveChat,
    PinMessage,
    PostAdmins,
    RemoveMember,
    SendAction,
    SendComment,
    SendMessage,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)

_LOADED_ROOTS: tuple[Any, ...] = (
    Updates,
    *dict.fromkeys(method.__returning__ for method in _METHOD_ROOTS),
)

_RetortT = TypeVar("_RetortT", bound=Retort)


def warming_up_retort(
    retort: _RetortT,
    warming_up: WarmingUpType | None = None,
) -> _RetortT:
    if warming_up is None:
        return retort

    roots: tuple[Any, ...]
    if warming_up is WarmingUpType.METHOD:
        roots = _METHOD_ROOTS
        retort_method = retort.get_dumper
    elif warming_up is WarmingUpType.TYPES:
        roots = _LOADED_ROOTS
        retort_method = retort.get_loader
    else:
        assert_never(warming_up)

    for root in roots:
        retort_method(root)

    return retort
