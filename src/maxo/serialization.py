import dataclasses
import typing
from collections.abc import Mapping
from datetime import UTC, datetime
from functools import cache
from typing import Any

from adaptix import Chain, P, Retort, dumper, loader
from adaptix.type_tools import exec_type_checking
from unihttp.serializers.adaptix.marker_tools import for_marker
from unihttp.serializers.adaptix.serialize import DEFAULT_RETORT

from maxo._internal.adaptix import concat_provider, has_tag_provider, is_subclass
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import QueryMarker
from maxo.enums import (
    AttachmentRequestType,
    AttachmentType,
    ButtonType,
    MarkupElementType,
    UpdateType,
)
from maxo.omit import Omitted
from maxo.types import (
    Attachments,
    AttachmentsRequests,
    AudioAttachment,
    AudioAttachmentRequest,
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    CallbackButton,
    ChatTitleChanged,
    ClipboardButton,
    CommentCreated,
    CommentEdited,
    CommentRemoved,
    ContactAttachment,
    ContactAttachmentRequest,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    EmphasizedMarkup,
    FileAttachment,
    FileAttachmentRequest,
    HeadingMarkup,
    HighlightedMarkup,
    InlineButtons,
    InlineKeyboardAttachment,
    InlineKeyboardAttachmentRequest,
    LinkButton,
    LinkMarkup,
    LocationAttachment,
    LocationAttachmentRequest,
    MarkupElements,
    MessageButton,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    MonospacedMarkup,
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
    Updates,
    UserAddedToChat,
    UserMentionMarkup,
    UserRemovedFromChat,
    VideoAttachment,
    VideoAttachmentRequest,
    base,
)
from maxo.types.facades import comment, message

_UPDATE_TAGS: Mapping[type, UpdateType] = {
    BotAddedToChat: UpdateType.BOT_ADDED,
    BotRemovedFromChat: UpdateType.BOT_REMOVED,
    BotStarted: UpdateType.BOT_STARTED,
    BotStopped: UpdateType.BOT_STOPPED,
    ChatTitleChanged: UpdateType.CHAT_TITLE_CHANGED,
    CommentCreated: UpdateType.COMMENT_CREATED,
    CommentEdited: UpdateType.COMMENT_EDITED,
    CommentRemoved: UpdateType.COMMENT_REMOVED,
    DialogCleared: UpdateType.DIALOG_CLEARED,
    DialogMuted: UpdateType.DIALOG_MUTED,
    DialogRemoved: UpdateType.DIALOG_REMOVED,
    DialogUnmuted: UpdateType.DIALOG_UNMUTED,
    MessageCallback: UpdateType.MESSAGE_CALLBACK,
    MessageCreated: UpdateType.MESSAGE_CREATED,
    MessageEdited: UpdateType.MESSAGE_EDITED,
    MessageRemoved: UpdateType.MESSAGE_REMOVED,
    UserAddedToChat: UpdateType.USER_ADDED,
    UserRemovedFromChat: UpdateType.USER_REMOVED,
}

_ATTACHMENT_TAGS: Mapping[type, AttachmentType] = {
    AudioAttachment: AttachmentType.AUDIO,
    ContactAttachment: AttachmentType.CONTACT,
    FileAttachment: AttachmentType.FILE,
    PhotoAttachment: AttachmentType.IMAGE,
    InlineKeyboardAttachment: AttachmentType.INLINE_KEYBOARD,
    LocationAttachment: AttachmentType.LOCATION,
    ShareAttachment: AttachmentType.SHARE,
    StickerAttachment: AttachmentType.STICKER,
    VideoAttachment: AttachmentType.VIDEO,
}

_MARKUP_TAGS: Mapping[type, MarkupElementType] = {
    EmphasizedMarkup: MarkupElementType.EMPHASIZED,
    LinkMarkup: MarkupElementType.LINK,
    MonospacedMarkup: MarkupElementType.MONOSPACED,
    StrikethroughMarkup: MarkupElementType.STRIKETHROUGH,
    StrongMarkup: MarkupElementType.STRONG,
    UnderlineMarkup: MarkupElementType.UNDERLINE,
    UserMentionMarkup: MarkupElementType.USER_MENTION,
    HeadingMarkup: MarkupElementType.HEADING,
    HighlightedMarkup: MarkupElementType.HIGHLIGHTED,
    QuoteMarkup: MarkupElementType.QUOTE,
}

_ATTACHMENT_REQUEST_TAGS: Mapping[type, AttachmentRequestType] = {
    PhotoAttachmentRequest: AttachmentRequestType.IMAGE,
    VideoAttachmentRequest: AttachmentRequestType.VIDEO,
    AudioAttachmentRequest: AttachmentRequestType.AUDIO,
    FileAttachmentRequest: AttachmentRequestType.FILE,
    StickerAttachmentRequest: AttachmentRequestType.STICKER,
    ContactAttachmentRequest: AttachmentRequestType.CONTACT,
    InlineKeyboardAttachmentRequest: AttachmentRequestType.INLINE_KEYBOARD,
    LocationAttachmentRequest: AttachmentRequestType.LOCATION,
    ShareAttachmentRequest: AttachmentRequestType.SHARE,
}

_BUTTON_TAGS: Mapping[type, ButtonType] = {
    CallbackButton: ButtonType.CALLBACK,
    LinkButton: ButtonType.LINK,
    RequestContactButton: ButtonType.REQUEST_CONTACT,
    RequestGeoLocationButton: ButtonType.REQUEST_GEO_LOCATION,
    OpenAppButton: ButtonType.OPEN_APP,
    MessageButton: ButtonType.MESSAGE,
    ClipboardButton: ButtonType.CLIPBOARD,
}

# (тип объединения, поле с тегом, {член: значение тега})
_TAG_GROUPS: tuple[tuple[Any, str, Mapping[type, Any]], ...] = (
    (Updates, "update_type", _UPDATE_TAGS),
    (Attachments, "type", _ATTACHMENT_TAGS),
    (MarkupElements, "type", _MARKUP_TAGS),
    (AttachmentsRequests, "type", _ATTACHMENT_REQUEST_TAGS),
    (InlineButtons, "type", _BUTTON_TAGS),
)

TAG_PROVIDERS = concat_provider(
    *(
        has_tag_provider(member, tag_field, value)
        for _union, tag_field, members in _TAG_GROUPS
        for member, value in members.items()
    ),
)


def create_retort() -> Retort:
    def _load_datetime(time: int) -> datetime:
        try:
            return datetime.fromtimestamp(time / 1000, tz=UTC)
        except (OSError, OverflowError, ValueError):
            if time > 0:
                return datetime.max.replace(tzinfo=UTC)
            return datetime.min.replace(tzinfo=UTC)

    exec_type_checking(base)
    exec_type_checking(comment)
    exec_type_checking(message)

    extended = DEFAULT_RETORT.extend(
        recipe=[
            TAG_PROVIDERS,
            dumper(
                is_subclass(MaxoMethod),
                _omit_none_query_values,
                chain=Chain.FIRST,
            ),
            dumper(
                for_marker(QueryMarker, P[bool]),
                int,
            ),
            dumper(
                for_marker(QueryMarker, P[list[str]] | P[list[int]]),
                lambda seq: ",".join(str(el) for el in seq),
            ),
            dumper(
                for_marker(QueryMarker, P[datetime]),  # Для GetComments
                lambda time: int(time.timestamp() * 1000),
            ),
            dumper(
                P[AttachmentsRequests | Attachments],
                lambda x: x.to_request() if isinstance(x, Attachments) else x,
                chain=Chain.FIRST,
            ),
            loader(P[datetime], _load_datetime),
        ],
    )

    return typing.cast(Retort, extended)


@cache
def get_retort() -> Retort:
    return create_retort()


def _omit_none_query_values(method: MaxoMethod[object]) -> MaxoMethod[object]:
    replacements = {
        field.name: Omitted()
        for field in dataclasses.fields(method)
        if any(
            isinstance(argument, QueryMarker)
            for argument in typing.get_args(field.type)
        )
        and getattr(method, field.name) is None
    }

    if not replacements:
        return method

    return dataclasses.replace(method, **replacements)
