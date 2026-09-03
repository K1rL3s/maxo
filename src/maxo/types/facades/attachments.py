import asyncio
from collections.abc import Callable, Sequence
from typing import TypeAlias

from unihttp.http import UploadFile

from maxo import loggers
from maxo.enums import UploadType
from maxo.errors.api import RetvalReturnedServerException
from maxo.omit import is_defined
from maxo.types.attachments import AttachmentsRequests, MediaAttachmentsRequests
from maxo.types.audio_attachment_request import AudioAttachmentRequest
from maxo.types.base import BaseMethodsFacade
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
MediaAttachmentFactory: TypeAlias = Callable[[str], MediaAttachmentsRequests]

MEDIA_ATTACHMENT_FACTORIES: dict[UploadType, MediaAttachmentFactory] = {
    UploadType.FILE: FileAttachmentRequest.factory,
    UploadType.AUDIO: AudioAttachmentRequest.factory,
    UploadType.VIDEO: VideoAttachmentRequest.factory,
    UploadType.IMAGE: lambda token: PhotoAttachmentRequest.factory(token=token),
}


class AttachmentsFacade(BaseMethodsFacade):
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
                    payload=InlineKeyboardAttachmentRequestPayload(
                        buttons=[list(row) for row in keyboard],
                    ),
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
            # Размер каждого файла считаем один раз и прокидываем дальше
            sizes = await asyncio.gather(*(file.size() for file in files_to_upload))
            uploaded_files = await self.build_media_attachments(files_to_upload, sizes)
            for i, uploaded_file in zip(file_indices, uploaded_files, strict=True):
                attachments[i] = uploaded_file

            await self._wait_media_processing(files_to_upload, sizes)

        return [attachment for attachment in attachments if attachment is not None]

    async def _wait_media_processing(
        self,
        files: Sequence[InputFile],
        sizes: Sequence[int],
    ) -> None:
        """Делает первичную паузу перед отправкой загруженных файлов."""
        config = self.bot.upload_config
        delays = [
            config.estimated_processing_delay(file.type, size)
            for file, size in zip(files, sizes, strict=True)
        ]
        delay = max(delays, default=0.0)
        if delay > 0:
            await asyncio.sleep(delay)

    async def build_media_attachments(
        self,
        files: Sequence[InputFile],
        sizes: Sequence[int] | None = None,
    ) -> Sequence[MediaAttachmentsRequests]:
        attachments: list[MediaAttachmentsRequests] = []

        if sizes is None:
            sizes = await asyncio.gather(*(file.size() for file in files))

        result = await asyncio.gather(
            *(
                self.upload_media(file, size)
                for file, size in zip(files, sizes, strict=True)
            ),
        )

        for type_, token in result:
            factory = MEDIA_ATTACHMENT_FACTORIES.get(type_)
            if factory is None:
                loggers.utils.warning("Received unknown attachment type: %s", type_)
                continue

            attachments.append(factory(token))

        return attachments

    async def upload_media(
        self,
        file: InputFile,
        size: int | None = None,
    ) -> tuple[UploadType, str]:
        if size is None:
            size = await file.size()
        if size <= 0:
            msg = "Нельзя загрузить пустой файл"
            raise ValueError(msg)

        result: UploadEndpoint = await self.bot.get_upload_url(type=file.type)

        upload_result = await self._upload_file(file, result.url, size)

        token: str
        if is_defined(result.token):
            token = result.token
        elif upload_result is not None:
            token = upload_result.last_token
        else:
            raise RuntimeError("Could not get upload token")

        return file.type, token

    async def _upload_file(
        self,
        file: InputFile,
        url: str,
        size: int,
    ) -> UploadMediaResult | None:
        if self.bot.upload_config.should_use_resumable(size):
            return await self.bot.upload_media_resumable(url, file, size)

        try:
            return await self.bot.upload_media(
                upload_url=url,
                file=UploadFile(file=await file.read(), filename=file.file_name),
            )
        except RetvalReturnedServerException:
            return None
