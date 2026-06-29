from maxo import Bot
from maxo.dialogs.api.entities import MediaId
from maxo.dialogs.api.protocols import MediaIdStorageProtocol
from maxo.enums import AttachmentType, UploadType
from maxo.routing.mixins import AttachmentsFacade
from maxo.utils.upload_media import FSInputFile, InputFile


class DialogAttachmentsFacade(AttachmentsFacade):
    __slots__ = ("_media_id_storage",)

    def __init__(
        self,
        bot: Bot,
        media_id_storage: MediaIdStorageProtocol,
    ) -> None:
        super().__init__(bot)
        self._media_id_storage = media_id_storage

    async def upload_media(self, file: InputFile) -> tuple[UploadType, str]:
        type_, token = await super().upload_media(file)

        if isinstance(file, FSInputFile):
            await self._media_id_storage.save_media_id(
                path=file.path,
                url=None,
                type=AttachmentType(file.type.value),
                media_id=MediaId(token=token),
            )

        return type_, token
