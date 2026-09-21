from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.sticker_attachment_request_payload import (
    StickerAttachmentRequestPayload,
)


class StickerAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление стикера. Должен быть единственным вложением в сообщении

    Args:
        payload:
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.STICKER

    payload: StickerAttachmentRequestPayload

    @classmethod
    def factory(cls, code: str) -> Self:
        """
        Фабричный метод.

        Args:
            code: Код стикера

        """
        return cls(
            payload=StickerAttachmentRequestPayload(
                code=code,
            ),
        )
