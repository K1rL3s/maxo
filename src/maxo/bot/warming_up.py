import gc
import linecache
from collections.abc import Iterator
from contextlib import contextmanager
from enum import Enum
from typing import Any, TypeVar, assert_never

from adaptix import Retort

from maxo.bot.methods import (
    AnswerOnCallback,
    DeleteChat,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditMessage,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
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
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.types import (
    Attachment,
    AttachmentPayload,
    AttachmentRequest,
    Attachments,
    AudioAttachment,
    AudioAttachmentRequest,
    BaseMaxoType,
    BotCommand,
    BotInfo,
    Button,
    Callback,
    CallbackButton,
    Chat,
    ChatAdmin,
    ChatAdminsList,
    ChatButton,
    ChatList,
    ChatMember,
    ChatMembersList,
    ClipboardButton,
    ContactAttachment,
    ContactAttachmentPayload,
    ContactAttachmentRequest,
    ContactAttachmentRequestPayload,
    EmphasizedMarkup,
    FailedUserDetails,
    FileAttachment,
    FileAttachmentPayload,
    FileAttachmentRequest,
    GetPinnedMessageResult,
    GetSubscriptionsResult,
    Image,
    InlineButtons,
    InlineKeyboardAttachment,
    InlineKeyboardAttachmentRequest,
    InlineKeyboardAttachmentRequestPayload,
    Keyboard,
    LinkButton,
    LinkMarkup,
    LinkedMessage,
    LocationAttachment,
    LocationAttachmentRequest,
    MarkupElements,
    MaxoType,
    MediaAttachmentPayload,
    MediaAttachments,
    Message,
    MessageBody,
    MessageButton,
    MessageList,
    ModifyMembersResult,
    MonospacedMarkup,
    NewMessageBody,
    NewMessageLink,
    OpenAppButton,
    PhotoAttachment,
    PhotoAttachmentPayload,
    PhotoAttachmentRequest,
    PhotoAttachmentRequestPayload,
    PhotoToken,
    QuoteMarkup,
    Recipient,
    RequestContactButton,
    RequestGeoLocationButton,
    SendMessageResult,
    ShareAttachment,
    ShareAttachmentPayload,
    ShareAttachmentRequest,
    SimpleQueryResult,
    StickerAttachment,
    StickerAttachmentPayload,
    StickerAttachmentRequest,
    StickerAttachmentRequestPayload,
    StrikethroughMarkup,
    StrongMarkup,
    Subscription,
    UnderlineMarkup,
    UpdateContext,
    UpdateList,
    UploadEndpoint,
    UploadMediaResult,
    UploadedInfo,
    User,
    UserMentionMarkup,
    UserWithPhoto,
    VideoAttachment,
    VideoAttachmentDetails,
    VideoAttachmentRequest,
    VideoThumbnail,
    VideoUrls,
)


class WarmingUpType(Enum):
    METHOD = "method"
    TYPES = "types"


_types = (
    Attachment,
    AttachmentPayload,
    AttachmentRequest,
    Attachments,
    AudioAttachment,
    AudioAttachmentRequest,
    BaseMaxoType,
    BotCommand,
    BotInfo,
    Button,
    InlineButtons,
    Callback,
    CallbackButton,
    Chat,
    ChatAdmin,
    ChatAdminsList,
    ChatButton,
    ChatList,
    ChatMember,
    ChatMembersList,
    ContactAttachment,
    ContactAttachmentPayload,
    ContactAttachmentRequest,
    ContactAttachmentRequestPayload,
    FileAttachment,
    FileAttachmentPayload,
    FileAttachmentRequest,
    GetPinnedMessageResult,
    GetSubscriptionsResult,
    Image,
    InlineKeyboardAttachment,
    InlineKeyboardAttachmentRequest,
    InlineKeyboardAttachmentRequestPayload,
    Keyboard,
    LinkButton,
    LinkedMessage,
    LocationAttachment,
    LocationAttachmentRequest,
    EmphasizedMarkup,
    FailedUserDetails,
    LinkMarkup,
    MarkupElements,
    MaxoType,
    MonospacedMarkup,
    StrikethroughMarkup,
    StrongMarkup,
    UnderlineMarkup,
    UserMentionMarkup,
    MediaAttachmentPayload,
    MediaAttachments,
    Message,
    MessageBody,
    MessageButton,
    MessageList,
    ModifyMembersResult,
    NewMessageBody,
    NewMessageLink,
    OpenAppButton,
    PhotoAttachment,
    PhotoAttachmentPayload,
    PhotoAttachmentRequest,
    PhotoAttachmentRequestPayload,
    PhotoToken,
    QuoteMarkup,
    Recipient,
    RequestContactButton,
    RequestGeoLocationButton,
    SendMessageResult,
    ShareAttachment,
    ShareAttachmentPayload,
    ShareAttachmentRequest,
    SimpleQueryResult,
    StickerAttachment,
    StickerAttachmentPayload,
    StickerAttachmentRequest,
    StickerAttachmentRequestPayload,
    Subscription,
    UpdateContext,
    UpdateList,
    UploadEndpoint,
    UploadedInfo,
    UploadMediaResult,
    User,
    UserWithPhoto,
    VideoAttachment,
    VideoAttachmentDetails,
    VideoAttachmentRequest,
    VideoThumbnail,
    VideoUrls,
    ClipboardButton,
)


_methods = (
    AnswerOnCallback,
    DeleteChat,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditMessage,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
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
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)

_RetortT = TypeVar("_RetortT", bound=Retort)


def _drop_generated_sources() -> None:
    for filename in tuple(linecache.cache):
        if filename.startswith("<adaptix generated "):
            linecache.cache.pop(filename, None)


@contextmanager
def eager_cycle_collection() -> Iterator[None]:
    """
    Заставляет сборщик циклов работать во время прогрева retort.

    Кодогенерация adaptix оставляет много циклического мусора: исключения
    `CannotProvide` с трейсбеками и фреймами. Полная сборка (поколение 2)
    запускается, когда доля новых долгоживущих объектов превышает четверть от
    всех долгоживущих. После `import maxo` их уже сотни тысяч, поэтому мусор
    прогрева успевает дожить до второго поколения и копится там до конца
    прогрева. Пик держит арены, которые CPython не отдаёт ОС, и этот пик
    становится постоянным RSS процесса.

    `gc.freeze()` переносит всё, что уже создано, в постоянное поколение.
    Счётчик долгоживущих объектов обнуляется, полные сборки начинают
    запускаться сразу, и мусор прогрева освобождается по ходу дела. На типах
    MAX это около 10 MB RSS без заметной потери скорости.

    Если процесс уже заморожен (типичный preload перед `fork` в gunicorn или
    uwsgi), ничего не трогаем: во-первых, оптимизация там уже работает,
    во-вторых, `gc.unfreeze()` сломал бы чужой copy-on-write.
    """
    if not gc.isenabled() or gc.get_freeze_count():
        yield
        return

    gc.freeze()
    try:
        yield
    finally:
        gc.unfreeze()


def warming_up_retort(
    retort: _RetortT,
    warming_up: WarmingUpType | None = None,
) -> _RetortT:
    if warming_up is None:
        return retort

    types: tuple[Any, ...]
    if warming_up is WarmingUpType.METHOD:
        types = _methods
        retort_method = retort.get_dumper
    elif warming_up is WarmingUpType.TYPES:
        types = _types
        retort_method = retort.get_loader
    else:
        assert_never(warming_up)

    for tp in types:
        retort_method(tp)  # type: ignore[arg-type]

    _drop_generated_sources()
    return retort
