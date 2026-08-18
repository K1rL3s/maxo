from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.uploaded_info import UploadedInfo


class FileAttachmentRequest(AttachmentRequest):
    """
    Данные для прикрепления файла к сообщению, которые вы получили в ответ на запрос [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads). Файл можно отправить только в комбинации с вложением с кнопками - отправка совместно с изображением или видео не поддерживается. При этом к сообщению можно прикрепить только один файл и одно вложение с кнопками. Подробнее - в описании [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads)

    Args:
        payload: Данные для прикрепления файла к сообщению, которые вы получили в ответ на запрос [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads). К сообщению можно прикрепить только один файл вместе с одним вложением с кнопками. Отправка файла совместно с другими вложениями не поддерживается
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.FILE

    payload: UploadedInfo
    """Данные для прикрепления файла к сообщению, которые вы получили в ответ на запрос [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads). К сообщению можно прикрепить только один файл вместе с одним вложением с кнопками. Отправка файла совместно с другими вложениями не поддерживается"""

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
