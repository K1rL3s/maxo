from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.uploaded_info import UploadedInfo


class FileAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление файла к сообщению. Должен быть единственным вложением в сообщении

    Args:
        payload:
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.FILE

    payload: UploadedInfo

    @classmethod
    def factory(cls, token: str) -> Self:
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
