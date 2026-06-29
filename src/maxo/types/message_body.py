from maxo.enums.attachment_type import AttachmentType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachments import Attachments
from maxo.types.audio_attachment import AudioAttachment
from maxo.types.base import MaxoType
from maxo.types.contact_attachment import ContactAttachment
from maxo.types.file_attachment import FileAttachment
from maxo.types.inline_keyboard_attachment import InlineKeyboardAttachment
from maxo.types.keyboard import Keyboard
from maxo.types.location_attachment import LocationAttachment
from maxo.types.markup_elements import MarkupElements
from maxo.types.photo_attachment import PhotoAttachment
from maxo.types.share_attachment import ShareAttachment
from maxo.types.sticker_attachment import StickerAttachment
from maxo.types.video_attachment import VideoAttachment
from maxo.utils.text_decorations import (
    TextDecoration,
    html_decoration,
    markdown_decoration,
)


class MessageBody(MaxoType):
    """
    Схема, представляющая тело сообщения

    Args:
        attachments: Вложения сообщения. Могут быть одним из типов `Attachment`. Смотрите описание схемы
        markup: Разметка текста сообщения. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)
        mid: Уникальный ID сообщения
        seq: ID последовательности сообщения в чате
        text: Новый текст сообщения
    """

    mid: str
    """Уникальный ID сообщения"""
    seq: int
    """ID последовательности сообщения в чате"""

    attachments: list[Attachments] | None = None
    """Вложения сообщения. Могут быть одним из типов `Attachment`. Смотрите описание схемы"""
    text: str | None = None
    """Новый текст сообщения"""

    markup: Omittable[list[MarkupElements] | None] = Omitted()
    """Разметка текста сообщения. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)"""

    @property
    def id(self) -> str:
        return self.mid

    @property
    def keyboard(self) -> Keyboard | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, InlineKeyboardAttachment):
                return attachment.payload
        return None

    @property
    def reply_markup(self) -> Keyboard | None:
        return self.keyboard

    @property
    def photo(self) -> list[PhotoAttachment]:
        return [
            attachment
            for attachment in self.attachments or []
            if isinstance(attachment, PhotoAttachment)
        ]

    @property
    def video(self) -> list[VideoAttachment]:
        return [
            attachment
            for attachment in self.attachments or []
            if isinstance(attachment, VideoAttachment)
        ]

    @property
    def audio(self) -> AudioAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, AudioAttachment):
                return attachment
        return None

    @property
    def file(self) -> FileAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, FileAttachment):
                return attachment
        return None

    @property
    def sticker(self) -> StickerAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, StickerAttachment):
                return attachment
        return None

    @property
    def contact(self) -> ContactAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, ContactAttachment):
                return attachment
        return None

    @property
    def share(self) -> ShareAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, ShareAttachment):
                return attachment
        return None

    @property
    def location(self) -> LocationAttachment | None:
        for attachment in self.attachments or []:
            if isinstance(attachment, LocationAttachment):
                return attachment
        return None

    def _unparse_entities(self, text_decoration: TextDecoration) -> str:
        text = self.text or ""
        entities = self.markup if is_defined(self.markup) else None
        return text_decoration.unparse(text=text, entities=entities)

    @property
    def html_text(self) -> str:
        return self._unparse_entities(html_decoration)

    @property
    def md_text(self) -> str:
        return self._unparse_entities(markdown_decoration)

    @property
    def unsafe_attachments(self) -> list[Attachments]:
        if is_defined(self.attachments):
            return self.attachments

        raise AttributeIsEmptyError(
            obj=self,
            attr="attachments",
        )

    @property
    def unsafe_markup(self) -> list[MarkupElements]:
        if is_defined(self.markup):
            return self.markup

        raise AttributeIsEmptyError(
            obj=self,
            attr="markup",
        )

    @property
    def unsafe_text(self) -> str:
        if is_defined(self.text):
            return self.text

        raise AttributeIsEmptyError(
            obj=self,
            attr="text",
        )

    @property
    def attachment_type(self) -> AttachmentType:
        if self.photo:
            return AttachmentType.PHOTO
        if self.video:
            return AttachmentType.VIDEO
        if self.audio:
            return AttachmentType.AUDIO
        if self.file:
            return AttachmentType.FILE
        if self.sticker:
            return AttachmentType.STICKER
        if self.contact:
            return AttachmentType.CONTACT
        if self.share:
            return AttachmentType.SHARE
        if self.location:
            return AttachmentType.LOCATION
        if self.text:
            return AttachmentType.TEXT
        return AttachmentType.UNKNOWN

    content_type = attachment_type  # Подражание aiogram
