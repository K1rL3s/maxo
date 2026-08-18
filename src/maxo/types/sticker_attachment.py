from typing import Self

from maxo.enums.attachment_type import AttachmentType
from maxo.types.attachment import Attachment
from maxo.types.sticker_attachment_payload import StickerAttachmentPayload
from maxo.types.sticker_attachment_request import StickerAttachmentRequest


class StickerAttachment(Attachment):
    """
    Args:
        height: Высота стикера
        payload: Результат отправки стикера
        type:
        width: Ширина стикера
    """

    type: AttachmentType = AttachmentType.STICKER

    height: int
    """Высота стикера"""
    payload: StickerAttachmentPayload
    """Результат отправки стикера"""
    width: int
    """Ширина стикера"""

    @classmethod
    def factory(
        cls,
        url: str,
        code: str,
        width: int,
        height: int,
    ) -> Self:
        """
        Фабричный метод.

        Args:
            url: URL медиа-вложения. Для видео-вложения используйте метод `GetVideoAttachmentDetails`, чтобы получить прямые ссылки.
            code: ID стикера.
            width: Ширина стикера.
            height: Высота стикера.

        """
        return cls(
            payload=StickerAttachmentPayload(
                url=url,
                code=code,
            ),
            width=width,
            height=height,
        )

    def to_request(self) -> StickerAttachmentRequest:
        return StickerAttachmentRequest.factory(code=self.payload.code)
