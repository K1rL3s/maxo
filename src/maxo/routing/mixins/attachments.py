import asyncio
from collections.abc import Sequence
from typing import TypeAlias

from unihttp.http import UploadFile

from maxo import loggers
from maxo.enums import UploadType
from maxo.errors.api import RetvalReturnedServerException
from maxo.omit import is_defined
from maxo.routing.mixins.subscription import SubscriptionMethodsFacade
from maxo.types.attachments import AttachmentsRequests, MediaAttachmentsRequests
from maxo.types.audio_attachment_request import AudioAttachmentRequest
from maxo.types.buttons import InlineButtons
from maxo.types.file_attachment_request import FileAttachmentRequest
from maxo.types.inline_keyboard_attachment_request import (
    InlineKeyboardAttachmentRequest,
)
from maxo.types.inline_keyboard_attachment_request_payload import (
    InlineKeyboardAttachmentRequestPayload,
)
from maxo.types.photo_attachment_request import PhotoAttachmentRequest
from maxo.types.upload_endpoint import UploadEndpoint
from maxo.types.upload_media_result import UploadMediaResult
from maxo.types.video_attachment_request import VideoAttachmentRequest
from maxo.utils.upload_media import InputFile

MediaInput: TypeAlias = InputFile | MediaAttachmentsRequests


class AttachmentsFacade(SubscriptionMethodsFacade):
    __slots__ = ()

    async def build_attachments(
        self,
        base: Sequence[AttachmentsRequests],
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        files: Sequence[MediaInput] | None = None,
    ) -> Sequence[AttachmentsRequests]:
        attachments = list(base)

        if keyboard is not None:
            attachments.append(
                InlineKeyboardAttachmentRequest(
                    payload=InlineKeyboardAttachmentRequestPayload(buttons=keyboard),
                ),
            )

        if files:
            attachments.extend(await self._build_media(files))

        return attachments

    async def _build_media(
        self,
        files: Sequence[MediaInput],
    ) -> list[MediaAttachmentsRequests]:
        attachments: list[MediaAttachmentsRequests | None] = [None] * len(files)
        files_to_upload: list[InputFile] = []
        file_indices: list[int] = []

        for i, file in enumerate(files):
            if isinstance(file, InputFile):
                files_to_upload.append(file)
                file_indices.append(i)
            else:
                attachments[i] = file

        if files_to_upload:
            uploaded_files = await self.build_media_attachments(files_to_upload)
            for i, uploaded_file in zip(file_indices, uploaded_files, strict=True):
                attachments[i] = uploaded_file

            # TODO: Исправить костыль со сном, https://github.com/K1rL3s/maxo/issues/10
            # maxo.errors.api.MaxBotBadRequestError:
            # ('attachment.not.ready',
            # 'Key: errors.process.attachment.file.not.processed')
            await asyncio.sleep(0.5)

        return [attachment for attachment in attachments if attachment is not None]

    async def build_media_attachments(
        self,
        files: Sequence[InputFile],
    ) -> Sequence[MediaAttachmentsRequests]:
        attachments: list[MediaAttachmentsRequests] = []

        result = await asyncio.gather(*(self.upload_media(file) for file in files))

        for type_, token in result:
            match type_:
                case UploadType.FILE:
                    attachments.append(FileAttachmentRequest.factory(token))
                case UploadType.AUDIO:
                    attachments.append(AudioAttachmentRequest.factory(token))
                case UploadType.VIDEO:
                    attachments.append(VideoAttachmentRequest.factory(token))
                case UploadType.IMAGE:
                    attachments.append(PhotoAttachmentRequest.factory(token=token))
                case _:
                    loggers.utils.warning("Received unknown attachment type: %s", type_)

        return attachments

    async def upload_media(self, file: InputFile) -> tuple[UploadType, str]:
        result: UploadEndpoint = await self.bot.get_upload_url(type=file.type)

        upload_result: UploadMediaResult | None
        try:
            upload_result = await self.bot.upload_media(
                upload_url=result.url,
                file=UploadFile(file=await file.read(), filename=file.file_name),
            )
        except RetvalReturnedServerException:
            upload_result = None

        token: str
        if is_defined(result.token):
            token = result.token
        elif upload_result is not None:
            token = upload_result.last_token
        else:
            raise RuntimeError("Could not get upload token")

        return file.type, token
