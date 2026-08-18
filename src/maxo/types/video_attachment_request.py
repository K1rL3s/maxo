from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.omit import Omittable, Omitted
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.uploaded_info import UploadedInfo


class VideoAttachmentRequest(AttachmentRequest):
    """
    Данные для прикрепления видео к сообщению. Вместе с видео можно прикрепить изображения (`type: image`) и одно вложение с кнопками (`type: inline_keyboard`). Общее количество вложений не должно превышать общее ограничение - 12. Подробнее - [в примерах](https://dev.max.ru/docs-api#Примеры%20с%20видео,%20изображением,%20файлом)

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
