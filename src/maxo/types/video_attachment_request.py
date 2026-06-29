from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.omit import Omittable, Omitted
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.uploaded_info import UploadedInfo


class VideoAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление видео к сообщению

    Args:
        payload:
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.VIDEO

    payload: UploadedInfo

    @classmethod
    def factory(cls, token: Omittable[str] = Omitted()) -> Self:
        """
        Фабричный метод.

        Args:
            token: Токен - уникальный ID загруженного медиафайла.

        """
        return cls(
            payload=UploadedInfo(
                token=token,
            ),
        )
