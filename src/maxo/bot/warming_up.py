from collections.abc import Iterable
from typing import Any

from unihttp.method import BaseMethod

from maxo.bot.methods import (
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
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.types import Attachments, Updates

_METHOD_ROOTS: tuple[type[BaseMethod[Any]], ...] = (
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
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)

# `list[Attachments]` - диалоги гоняют вложения в сторадж мимо методов
_DUMPED_ROOTS: tuple[Any, ...] = (*_METHOD_ROOTS, list[Attachments])

_LOADED_ROOTS: tuple[Any, ...] = (
    Updates,
    list[Attachments],
    *dict.fromkeys(method.__returning__ for method in _METHOD_ROOTS),
)


def warm_up(
    *,
    loaded: Iterable[type] | None = None,
    dumped: Iterable[type] | None = None,
) -> None:
    from maxo.serialization import get_retort  # noqa: PLC0415 - avoids import cycle

    retort = get_retort()

    for type_ in _LOADED_ROOTS if loaded is None else loaded:
        retort.get_loader(type_)
    for type_ in _DUMPED_ROOTS if dumped is None else dumped:
        retort.get_dumper(type_)
