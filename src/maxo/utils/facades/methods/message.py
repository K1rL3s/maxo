import asyncio
from abc import ABC, abstractmethod
from collections.abc import Sequence

from maxo.bot.method_results.messages.delete_message import DeleteMessageResult
from maxo.enums import MessageLinkType, TextFormat, UploadType
from maxo.loggers import utils as logger
from maxo.omit import Omittable, Omitted
from maxo.types import (
    AudioAttachmentRequest,
    FileAttachmentRequest,
    ImageAttachmentRequest,
    VideoAttachmentRequest,
)
from maxo.types.inline_keyboard_attachment_request import (
    InlineKeyboardAttachmentRequest,
)
from maxo.types.inline_keyboard_attachment_request_payload import (
    InlineKeyboardAttachmentRequestPayload,
)
from maxo.types.keyboard_buttons import KeyboardButtons
from maxo.types.message import Message
from maxo.types.new_message_link import NewMessageLink
from maxo.types.request_attachments import AttachmentsRequests, MediaAttachmentsRequests
from maxo.utils.facades.methods.base import BaseMethodsFacade
from maxo.utils.facades.methods.upload_media import UploadMediaFacade
from maxo.utils.helpers.calculating import calculate_chat_id_and_user_id
from maxo.utils.upload_media import InputFile


class MessageMethodsFacade(BaseMethodsFacade, ABC):
    @property
    @abstractmethod
    def message(self) -> Message:
        raise NotImplementedError

    async def delete_message(self) -> DeleteMessageResult:
        message_id = self.message.unsafe_body.mid
        return await self.bot.delete_message(message_id=message_id)

    async def send_message(
        self,
        text: str | None = None,
        link: NewMessageLink | None = None,
        notify: Omittable[bool] = True,
        format: TextFormat | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        media: Sequence[InputFile] | None = None,
    ) -> Message:
        recipient = self.message.recipient
        chat_id, user_id = calculate_chat_id_and_user_id(
            chat_id=recipient.chat_id,
            user_id=recipient.user_id,
            chat_type=recipient.chat_type,
        )

        attachments = await self._build_attachments(
            base=[],
            keyboard=keyboard,
            media=media,
        )

        result = await self.bot.send_message(
            chat_id=chat_id or Omitted(),
            user_id=user_id or Omitted(),
            text=text,
            attachments=attachments,
            link=link,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    async def answer_text(
        self,
        text: str,
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: TextFormat | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> Message:
        return await self.send_message(
            text=text,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
        )

    async def reply_text(
        self,
        text: str,
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: TextFormat | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> Message:
        return await self.send_message(
            text=text,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
            link=self._make_new_message_link(MessageLinkType.REPLY),
        )

    async def send_media(
        self,
        media: InputFile | Sequence[InputFile],
        text: str | None = None,
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: TextFormat | None = None,
        link: NewMessageLink | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> Message:
        if isinstance(media, InputFile):
            media = (media,)

        return await self.send_message(
            text=text,
            media=media,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
            link=link,
        )

    async def edit_message(
        self,
        text: str | None = None,
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        media: Sequence[InputFile] | None = None,
        link: NewMessageLink | None = None,
        notify: bool = True,
        format: TextFormat | None = None,
    ) -> Message:
        message_id = self.message.unsafe_body.mid

        if text is None:
            text = self.message.unsafe_body.text

        attachments = await self._build_attachments(
            base=[],
            keyboard=keyboard,
            media=media,
        )

        return await self.bot.edit_message(
            message_id=message_id,
            text=text,
            attachments=attachments,
            link=link,
            notify=notify,
            format=format,
        )

    def _make_new_message_link(self, type: MessageLinkType) -> NewMessageLink:
        return NewMessageLink(
            type=type,
            mid=self.message.unsafe_body.mid,
        )

    async def _build_attachments(
        self,
        base: Sequence[AttachmentsRequests],
        keyboard: Sequence[Sequence[KeyboardButtons]] | None = None,
        media: Sequence[InputFile] | None = None,
    ) -> Sequence[AttachmentsRequests]:
        attachments = list(base)

        if keyboard is not None:
            attachments.append(
                InlineKeyboardAttachmentRequest(
                    payload=InlineKeyboardAttachmentRequestPayload(buttons=keyboard),
                ),
            )

        if media:
            attachments.extend(await self._build_media_attachments(media))
            # TODO: Костыль
            # maxo.errors.api.MaxBotBadRequestError:
            # ('attachment.not.ready', 'Key: errors.process.attachment.file.not.processed')
            await asyncio.sleep(0.5)

        return attachments

    async def _build_media_attachments(
        self,
        media: Sequence[InputFile],
    ) -> Sequence[MediaAttachmentsRequests]:
        attachments: list[MediaAttachmentsRequests] = []

        result = await asyncio.gather(
            *(self._upload_media(upload_media) for upload_media in media),
        )

        for type_, token in result:
            match type_:
                case UploadType.FILE:
                    attachments.append(FileAttachmentRequest.factory(token))
                case UploadType.AUDIO:
                    attachments.append(AudioAttachmentRequest.factory(token))
                case UploadType.VIDEO:
                    attachments.append(VideoAttachmentRequest.factory(token))
                case UploadType.IMAGE:
                    attachments.append(ImageAttachmentRequest.factory(token=token))
                case _:
                    logger.warning("Received unknown attachment type: %s", type_)

        return attachments

    async def _upload_media(self, media: InputFile) -> tuple[UploadType, str]:
        token = await UploadMediaFacade(self.bot, media).upload()
        return media.type, token.last_token
