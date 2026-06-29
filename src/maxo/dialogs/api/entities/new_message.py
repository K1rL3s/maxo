from dataclasses import field
from enum import Enum

from maxo.dialogs.api.entities import MediaAttachment, ShowMode
from maxo.dialogs.api.entities.link_preview import LinkPreviewOptions
from maxo.enums import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types import (
    Attachments,
    InlineButtons,
    InlineKeyboardAttachment,
    MaxoType,
    MediaAttachments,
    NewMessageLink,
    Recipient,
)

MarkupVariant = list[list[InlineButtons]]


class UnknownText(Enum):
    UNKNOWN = object()


class OldMessage(MaxoType):
    recipient: Recipient
    message_id: str
    sequence_id: int
    text: str | None | UnknownText
    attachments: list[Attachments]

    @property
    def keyboard(self) -> MarkupVariant | None:
        for attachment in self.attachments:
            if isinstance(attachment, InlineKeyboardAttachment):
                return attachment.payload.buttons
        return None

    @property
    def media(self) -> list[MediaAttachments]:
        return [
            attachment
            for attachment in self.attachments
            if isinstance(attachment, MediaAttachments)
        ]


class NewMessage(MaxoType):
    recipient: Recipient
    keyboard: MarkupVariant | None = None
    media: list[MediaAttachment] = field(default_factory=list)
    parse_mode: Omittable[TextFormat | None] = Omitted()
    link_preview_options: LinkPreviewOptions | None = None
    show_mode: ShowMode = ShowMode.AUTO
    text: str | None = None
    link_to: NewMessageLink | None = None
