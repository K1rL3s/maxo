from dataclasses import field
from typing import Self

from maxo.enums.attachment_type import AttachmentType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachment import Attachment
from maxo.types.share_attachment_payload import ShareAttachmentPayload
from maxo.types.share_attachment_request import ShareAttachmentRequest


class ShareAttachment(Attachment):
    """
    Args:
        description: Описание предпросмотра ссылки
        image_url: Изображение предпросмотра ссылки
        payload: Данные, использованные для прикрепления к сообщению предпросмотра контента по внешнему URL
        title: Заголовок предпросмотра ссылки.
        type:
    """

    type: AttachmentType = AttachmentType.SHARE

    payload: ShareAttachmentPayload = field(default_factory=ShareAttachmentPayload)
    """Данные, использованные для прикрепления к сообщению предпросмотра контента по внешнему URL"""

    description: Omittable[str | None] = Omitted()
    """Описание предпросмотра ссылки"""
    image_url: Omittable[str | None] = Omitted()
    """Изображение предпросмотра ссылки"""
    title: Omittable[str | None] = Omitted()
    """Заголовок предпросмотра ссылки."""

    @classmethod
    def factory(
        cls,
        url: Omittable[str | None] = Omitted(),
        token: Omittable[str | None] = Omitted(),
        title: Omittable[str | None] = Omitted(),
        description: Omittable[str | None] = Omitted(),
        image_url: Omittable[str | None] = Omitted(),
    ) -> Self:
        return cls(
            payload=ShareAttachmentPayload(
                url=url,
                token=token,
            ),
            title=title,
            description=description,
            image_url=image_url,
        )

    @property
    def unsafe_description(self) -> str:
        if is_defined(self.description):
            return self.description

        raise AttributeIsEmptyError(
            obj=self,
            attr="description",
        )

    @property
    def unsafe_image_url(self) -> str:
        if is_defined(self.image_url):
            return self.image_url

        raise AttributeIsEmptyError(
            obj=self,
            attr="image_url",
        )

    @property
    def unsafe_title(self) -> str:
        if is_defined(self.title):
            return self.title

        raise AttributeIsEmptyError(
            obj=self,
            attr="title",
        )

    def to_request(self) -> ShareAttachmentRequest:
        return ShareAttachmentRequest.factory(
            token=self.payload.token,
            url=self.payload.url,
        )
