import dataclasses
import typing
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from adaptix import Chain, P, Retort, dumper, loader
from adaptix.type_tools import exec_type_checking
from unihttp.markers import QueryMarker
from unihttp.serializers.adaptix import DEFAULT_RETORT, for_marker

from maxo._internal.adaptix import concat_provider, has_tag_provider, is_subclass
from maxo.bot.defaults import BotDefaults
from maxo.bot.methods import EditMessage, SendMessage
from maxo.bot.warming_up import WarmingUpType, warming_up_retort
from maxo.enums import (
    AttachmentRequestType,
    AttachmentType,
    ButtonType,
    MarkupElementType,
    UpdateType,
)
from maxo.omit import is_omitted
from maxo.routing.updates import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    ChatTitleChanged,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
    UserRemovedFromChat,
)
from maxo.types import (
    Attachments,
    AttachmentsRequests,
    AudioAttachment,
    AudioAttachmentRequest,
    CallbackButton,
    ClipboardButton,
    ContactAttachment,
    ContactAttachmentRequest,
    EmphasizedMarkup,
    FileAttachment,
    FileAttachmentRequest,
    HeadingMarkup,
    HighlightedMarkup,
    InlineKeyboardAttachment,
    InlineKeyboardAttachmentRequest,
    LinkButton,
    LinkMarkup,
    LocationAttachment,
    LocationAttachmentRequest,
    MessageButton,
    MonospacedMarkup,
    NewMessageBody,
    OpenAppButton,
    PhotoAttachment,
    PhotoAttachmentRequest,
    QuoteMarkup,
    RequestContactButton,
    RequestGeoLocationButton,
    ShareAttachment,
    ShareAttachmentRequest,
    StickerAttachment,
    StickerAttachmentRequest,
    StrikethroughMarkup,
    StrongMarkup,
    UnderlineMarkup,
    UserMentionMarkup,
    VideoAttachment,
    VideoAttachmentRequest,
    base,
)

if TYPE_CHECKING:
    from maxo import Bot


TAG_PROVIDERS = concat_provider(
    # ---> UpdateType <---
    has_tag_provider(BotAddedToChat, "update_type", UpdateType.BOT_ADDED),
    has_tag_provider(BotRemovedFromChat, "update_type", UpdateType.BOT_REMOVED),
    has_tag_provider(BotStarted, "update_type", UpdateType.BOT_STARTED),
    has_tag_provider(BotStopped, "update_type", UpdateType.BOT_STOPPED),
    has_tag_provider(ChatTitleChanged, "update_type", UpdateType.CHAT_TITLE_CHANGED),
    has_tag_provider(DialogCleared, "update_type", UpdateType.DIALOG_CLEARED),
    has_tag_provider(DialogMuted, "update_type", UpdateType.DIALOG_MUTED),
    has_tag_provider(DialogRemoved, "update_type", UpdateType.DIALOG_REMOVED),
    has_tag_provider(DialogUnmuted, "update_type", UpdateType.DIALOG_UNMUTED),
    has_tag_provider(MessageCallback, "update_type", UpdateType.MESSAGE_CALLBACK),
    has_tag_provider(MessageCreated, "update_type", UpdateType.MESSAGE_CREATED),
    has_tag_provider(MessageEdited, "update_type", UpdateType.MESSAGE_EDITED),
    has_tag_provider(MessageRemoved, "update_type", UpdateType.MESSAGE_REMOVED),
    has_tag_provider(UserAddedToChat, "update_type", UpdateType.USER_ADDED),
    has_tag_provider(UserRemovedFromChat, "update_type", UpdateType.USER_REMOVED),
    # ---> AttachmentType <---
    has_tag_provider(AudioAttachment, "type", AttachmentType.AUDIO),
    has_tag_provider(ContactAttachment, "type", AttachmentType.CONTACT),
    has_tag_provider(FileAttachment, "type", AttachmentType.FILE),
    has_tag_provider(PhotoAttachment, "type", AttachmentType.IMAGE),
    has_tag_provider(InlineKeyboardAttachment, "type", AttachmentType.INLINE_KEYBOARD),
    has_tag_provider(LocationAttachment, "type", AttachmentType.LOCATION),
    has_tag_provider(ShareAttachment, "type", AttachmentType.SHARE),
    has_tag_provider(StickerAttachment, "type", AttachmentType.STICKER),
    has_tag_provider(VideoAttachment, "type", AttachmentType.VIDEO),
    # ---> MarkupElementType <---
    has_tag_provider(EmphasizedMarkup, "type", MarkupElementType.EMPHASIZED),
    has_tag_provider(LinkMarkup, "type", MarkupElementType.LINK),
    has_tag_provider(MonospacedMarkup, "type", MarkupElementType.MONOSPACED),
    has_tag_provider(StrikethroughMarkup, "type", MarkupElementType.STRIKETHROUGH),
    has_tag_provider(StrongMarkup, "type", MarkupElementType.STRONG),
    has_tag_provider(UnderlineMarkup, "type", MarkupElementType.UNDERLINE),
    has_tag_provider(UserMentionMarkup, "type", MarkupElementType.USER_MENTION),
    has_tag_provider(HeadingMarkup, "type", MarkupElementType.HEADING),
    has_tag_provider(HighlightedMarkup, "type", MarkupElementType.HIGHLIGHTED),
    has_tag_provider(QuoteMarkup, "type", MarkupElementType.QUOTE),
    # ---> AttachmentRequestType <---
    has_tag_provider(PhotoAttachmentRequest, "type", AttachmentRequestType.IMAGE),
    has_tag_provider(VideoAttachmentRequest, "type", AttachmentRequestType.VIDEO),
    has_tag_provider(AudioAttachmentRequest, "type", AttachmentRequestType.AUDIO),
    has_tag_provider(FileAttachmentRequest, "type", AttachmentRequestType.FILE),
    has_tag_provider(StickerAttachmentRequest, "type", AttachmentRequestType.STICKER),
    has_tag_provider(ContactAttachmentRequest, "type", AttachmentRequestType.CONTACT),
    has_tag_provider(
        InlineKeyboardAttachmentRequest,
        "type",
        AttachmentRequestType.INLINE_KEYBOARD,
    ),
    has_tag_provider(LocationAttachmentRequest, "type", AttachmentRequestType.LOCATION),
    has_tag_provider(ShareAttachmentRequest, "type", AttachmentRequestType.SHARE),
    # ---> KeyboardButtonType <---
    has_tag_provider(CallbackButton, "type", ButtonType.CALLBACK),
    has_tag_provider(LinkButton, "type", ButtonType.LINK),
    has_tag_provider(RequestContactButton, "type", ButtonType.REQUEST_CONTACT),
    has_tag_provider(RequestGeoLocationButton, "type", ButtonType.REQUEST_GEO_LOCATION),
    has_tag_provider(OpenAppButton, "type", ButtonType.OPEN_APP),
    has_tag_provider(MessageButton, "type", ButtonType.MESSAGE),
    has_tag_provider(ClipboardButton, "type", ButtonType.CLIPBOARD),
)


def _create_retort(*, defaults: BotDefaults | None = None) -> Retort:
    if defaults is None:
        defaults = BotDefaults()

    types_with_defaults = SendMessage | EditMessage | NewMessageBody

    def _set_method_defaults(method: types_with_defaults) -> types_with_defaults:
        if hasattr(method, "format") and is_omitted(method.format):
            method = dataclasses.replace(method, format=defaults.text_format)
        if hasattr(method, "disable_link_preview") and is_omitted(
            method.disable_link_preview,
        ):
            method = dataclasses.replace(
                method,
                disable_link_preview=defaults.disable_link_preview,
            )
        return method

    def _load_datetime(time: int) -> datetime:
        try:
            return datetime.fromtimestamp(time / 1000, tz=UTC)
        except (OSError, OverflowError, ValueError):
            if time > 0:
                return datetime.max.replace(tzinfo=UTC)
            return datetime.min.replace(tzinfo=UTC)

    exec_type_checking(base)

    return DEFAULT_RETORT.extend(
        recipe=[
            TAG_PROVIDERS,
            dumper(
                for_marker(QueryMarker, P[None]),
                lambda _: "null",
            ),
            dumper(
                for_marker(QueryMarker, P[bool]),
                lambda item: int(item),
            ),
            dumper(
                for_marker(QueryMarker, P[list[str]] | P[list[int]]),
                lambda seq: ",".join(str(el) for el in seq),
            ),
            dumper(
                P[*typing.get_args(types_with_defaults)],
                _set_method_defaults,
                chain=Chain.FIRST,
            ),
            dumper(
                P[AttachmentsRequests | Attachments],
                lambda x: x.to_request() if isinstance(x, Attachments) else x,
                chain=Chain.FIRST,
            ),
            loader(P[datetime], _load_datetime),
        ],
    )


def create_retort(
    *,
    defaults: BotDefaults | None = None,
    warming_up: bool = True,
) -> Retort:
    retort = _create_retort(defaults=defaults)

    if warming_up:
        retort = warming_up_retort(retort, warming_up=WarmingUpType.TYPES)
        retort = warming_up_retort(retort, warming_up=WarmingUpType.METHOD)

    return typing.cast(Retort, retort)


def create_retort_with_bot(
    bot: "Bot",
    *,
    defaults: BotDefaults | None = None,
    warming_up: bool = True,
) -> Retort:
    def _load_bot[T: base.MaxoType](x: T) -> T:
        return x.as_(bot)

    retort = _create_retort(defaults=defaults)

    retort = retort.extend(
        recipe=[loader(is_subclass(base.MaxoType), _load_bot, Chain.LAST)],
    )

    if warming_up:
        retort = warming_up_retort(retort, warming_up=WarmingUpType.TYPES)
        retort = warming_up_retort(retort, warming_up=WarmingUpType.METHOD)

    return typing.cast(Retort, retort)
