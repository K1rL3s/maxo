from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.omit import Omittable, Omitted
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.share_attachment_payload import ShareAttachmentPayload


class ShareAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление предпросмотра контента по внешнему URL

    Args:
        payload: Данные для прикрепления предпросмотра контента по внешнему URL
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.SHARE

    payload: ShareAttachmentPayload
    """Данные для прикрепления предпросмотра контента по внешнему URL"""

    @classmethod
    def factory(
        cls,
        *,
        url: Omittable[str | None] = Omitted(),
        token: Omittable[str | None] = Omitted(),
    ) -> Self:
        """
        Фабричный метод.

        Args:
            url: URL, прикрепленный к сообщению в качестве предпросмотра медиа. От 1 символа.
            token: Токен вложения.

        """
        return cls(
            payload=ShareAttachmentPayload(
                url=url,
                token=token,
            ),
        )
