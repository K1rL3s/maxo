import warnings
from collections.abc import Sequence

from maxo import Bot, loggers
from maxo.dialogs.api.entities import MediaAttachment, NewMessage, OldMessage, ShowMode
from maxo.dialogs.api.protocols import (
    MediaIdStorageProtocol,
    MessageManagerProtocol,
    MessageNotModified,
)
from maxo.dialogs.manager.attachment_facade import DialogAttachmentsFacade
from maxo.enums import AttachmentType, UploadType
from maxo.errors import MaxBotApiError, MaxBotBadRequestError
from maxo.omit import Omitted
from maxo.routing.mixins import MediaInput
from maxo.types import (
    AttachmentsRequests,
    AudioAttachmentRequest,
    Callback,
    FileAttachmentRequest,
    InlineButtons,
    MediaAttachments,
    MediaAttachmentsRequests,
    Message,
    PhotoAttachmentRequest,
    VideoAttachmentRequest,
)
from maxo.utils.upload_media import FSInputFile, InputFile

SEND_METHODS = {
    AttachmentType.AUDIO: "send_audio",
    AttachmentType.IMAGE: "send_photo",
    AttachmentType.VIDEO: "send_video",
    AttachmentType.STICKER: "send_sticker",
}

INPUT_MEDIA_TYPES = {}

_INVALID_QUERY_ID_MSG = (
    "query is too old and response timeout expired or query id is invalid"
)


def _combine(sent_message: NewMessage, message_result: Message) -> OldMessage:
    return OldMessage(
        message_id=message_result.body.mid,
        sequence_id=message_result.body.seq,
        recipient=message_result.recipient,
        text=message_result.body.text,
        attachments=message_result.body.attachments or [],
    )


class MessageManager(MessageManagerProtocol):
    def __init__(self, media_id_storage: MediaIdStorageProtocol) -> None:
        self.media_id_storage = media_id_storage

    async def answer_callback(
        self,
        bot: Bot,
        callback: Callback,
    ) -> None:
        try:
            await bot.answer_on_callback(
                callback_id=callback.callback_id,
                notification="",
            )
        except MaxBotApiError as e:
            if _INVALID_QUERY_ID_MSG in e.message.lower():
                loggers.dialogs.warning("Cannot answer callback: %s", e)
            else:
                raise

    def had_media(self, old_message: OldMessage) -> bool:
        return any(
            isinstance(media, MediaAttachments) for media in old_message.attachments
        )

    def need_media(self, new_message: NewMessage) -> bool:
        return bool(new_message.media)

    def _message_changed(
        self,
        new_message: NewMessage,
        old_message: OldMessage,
    ) -> bool:
        if (
            (new_message.text != old_message.text)
            or new_message.keyboard
            or
            # we do not know if link preview changed
            new_message.link_preview_options
        ):
            return True

        if self.had_media(old_message) != self.need_media(new_message):
            return True
        if not self.need_media(new_message):
            return False
        return False

    def _can_edit(self, new_message: NewMessage, old_message: OldMessage) -> bool:
        return True

    async def show_message(
        self,
        bot: Bot,
        new_message: NewMessage,
        old_message: OldMessage | None,
    ) -> OldMessage:
        if new_message.show_mode is ShowMode.NO_UPDATE:
            loggers.dialogs.debug("ShowMode is NO_UPDATE, skipping show")
            raise MessageNotModified("ShowMode is NO_UPDATE")
        if old_message and new_message.show_mode is ShowMode.DELETE_AND_SEND:
            loggers.dialogs.debug(
                "Delete and send new message, because: mode=%s",
                new_message.show_mode,
            )
            await self.remove_message_safe(bot, old_message, new_message)
            sent_message = await self.send_message(bot, new_message)
            return _combine(new_message, sent_message)
        if not old_message or new_message.show_mode is ShowMode.SEND:
            loggers.dialogs.debug(
                "Send new message, because: mode=%s, has old_message=%s",
                new_message.show_mode,
                bool(old_message),
            )
            await self._remove_kbd(bot, old_message, new_message)
            sent_message = await self.send_message(bot, new_message)
            return _combine(new_message, sent_message)

        if not self._message_changed(new_message, old_message):
            loggers.dialogs.debug("Message did not change")
            # nothing changed: text, keyboard or media
            return old_message

        if not self._can_edit(new_message, old_message):
            await self.remove_message_safe(bot, old_message, new_message)
            sent_message = await self.send_message(bot, new_message)
            return _combine(new_message, sent_message)
        sent_message = await self.edit_message_safe(bot, new_message, old_message)
        return _combine(new_message, sent_message)

    # Clear
    async def remove_kbd(
        self,
        bot: Bot,
        show_mode: ShowMode,
        old_message: OldMessage | None,
    ) -> None:
        if show_mode is ShowMode.NO_UPDATE:
            return
        if show_mode is ShowMode.DELETE_AND_SEND and old_message:
            await self.remove_message_safe(bot, old_message, None)
            return
        await self._remove_kbd(bot, old_message, None)

    async def _remove_kbd(
        self,
        bot: Bot,
        old_message: OldMessage | None,
        new_message: NewMessage | None,
    ) -> None:
        await self.remove_inline_kbd(bot, old_message)

    async def remove_inline_kbd(
        self,
        bot: Bot,
        old_message: OldMessage | None,
    ) -> None:
        if not old_message or old_message.keyboard is None:
            return
        loggers.dialogs.debug("remove_inline_kbd in %s", old_message.recipient)
        try:
            new_attachments = [
                attach.to_request()
                for attach in old_message.attachments
                if attach.type != AttachmentType.INLINE_KEYBOARD
            ]
            await bot.edit_message(
                message_id=old_message.message_id,
                attachments=new_attachments,
            )
        except MaxBotBadRequestError as err:
            if "message is not modified" in err.message:
                return  # клавиатуры уже не было
            if (
                "message can't be edited" in err.message
                or "message to edit not found" in err.message
                or "MESSAGE_ID_INVALID" in err.message
            ):
                return
            raise

    async def remove_message_safe(
        self,
        bot: Bot,
        old_message: OldMessage,
        new_message: NewMessage | None,
    ) -> None:
        try:
            await bot.delete_message(
                message_id=old_message.message_id,
            )
        except MaxBotBadRequestError as err:
            if "message to delete not found" in err.message:
                pass
            elif "message can't be deleted" in err.message:
                await self._remove_kbd(bot, old_message, new_message)
            else:
                raise

    async def edit_message_safe(
        self,
        bot: Bot,
        new_message: NewMessage,
        old_message: OldMessage,
    ) -> Message:
        try:
            return await self.edit_message(bot, new_message, old_message)
        except MaxBotBadRequestError as err:
            if "message is not modified" in err.message:
                raise MessageNotModified from err
            if (
                "message can't be edited" in err.message
                or "message to edit not found" in err.message
            ):
                return await self.send_message(bot, new_message)
            raise

    async def edit_message(
        self,
        bot: Bot,
        new_message: NewMessage,
        old_message: OldMessage,
    ) -> Message:
        attachments = await self._build_attachments(
            bot,
            new_message.keyboard,
            new_message.media,
        )
        await bot.edit_message(
            link=new_message.link_to,
            message_id=old_message.message_id,
            text=new_message.text,
            attachments=attachments,
            format=new_message.parse_mode,
        )
        return await bot.get_message_by_id(message_id=old_message.message_id)

    async def send_message(self, bot: Bot, new_message: NewMessage) -> Message:
        if new_message.link_preview_options:
            disable_link_preview = new_message.link_preview_options.is_disabled
        else:
            disable_link_preview = Omitted()

        attachments = await self._build_attachments(
            bot,
            new_message.keyboard,
            new_message.media,
        )
        result = await bot.send_message(
            chat_id=new_message.recipient.chat_id,
            user_id=new_message.recipient.user_id,
            text=new_message.text,
            link=new_message.link_to,
            notify=True,
            attachments=attachments,
            format=new_message.parse_mode,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    async def _build_attachments(
        self,
        bot: Bot,
        keyboard: Sequence[Sequence[InlineButtons]] | None,
        media: list[MediaAttachment],
    ) -> Sequence[AttachmentsRequests]:
        converted_media = [self._convert_media(m) for m in media]
        base: list[MediaAttachmentsRequests] = []
        files: list[InputFile] = []
        for attach in converted_media:
            if isinstance(attach, InputFile):
                files.append(attach)
            elif isinstance(attach, MediaAttachmentsRequests):
                base.append(attach)

        facade = DialogAttachmentsFacade(bot, media_id_storage=self.media_id_storage)
        return await facade.build_attachments(base=base, keyboard=keyboard, files=files)

    def _convert_media(self, media: MediaAttachment) -> MediaInput | None:
        if media.media_id:
            token = media.media_id.token
            url = None
        elif media.url:
            if media.type != AttachmentType.IMAGE:
                raise ValueError(
                    f"URL is supported only for IMAGE media, got: {media.type}",
                )
            token = None
            url = media.url
        elif media.path:
            if media.type not in (
                AttachmentType.IMAGE,
                AttachmentType.VIDEO,
                AttachmentType.AUDIO,
                AttachmentType.FILE,
            ):
                raise ValueError(f"Unsupported media type for file path: {media.type}")
            return FSInputFile(media.path, UploadType(media.type))
        else:
            return None

        if media.type == AttachmentType.IMAGE:
            return PhotoAttachmentRequest.factory(token=token, url=url)
        if media.type == AttachmentType.VIDEO:
            return VideoAttachmentRequest.factory(token=token)
        if media.type == AttachmentType.AUDIO:
            return AudioAttachmentRequest.factory(token=token)
        if media.type == AttachmentType.FILE:
            return FileAttachmentRequest.factory(token=token)

        warnings.warn(
            f"Unknown media attachment type: {media.type}",
            category=RuntimeWarning,
            stacklevel=2,
        )
        return None
