from typing import Self

from maxo.enums.attachment_type import AttachmentType
from maxo.enums.video_type import VideoType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined, is_not_omitted
from maxo.types.attachment import Attachment
from maxo.types.media_attachment_payload import MediaAttachmentPayload
from maxo.types.video_attachment_request import VideoAttachmentRequest
from maxo.types.video_thumbnail import VideoThumbnail


class VideoAttachment(Attachment):
    """
    Args:
        duration: Длина видео в секундах
        height: Высота видео
        payload:
        thumbnail: Миниатюра видео
        type:
        video_type: Тип видео: обычное видео или видеосообщение
        width: Ширина видео
    """

    type: AttachmentType = AttachmentType.VIDEO

    payload: MediaAttachmentPayload

    duration: Omittable[int | None] = Omitted()
    """Длина видео в секундах"""
    height: Omittable[int | None] = Omitted()
    """Высота видео"""
    thumbnail: Omittable[VideoThumbnail | None] = Omitted()
    """Миниатюра видео"""
    video_type: Omittable[VideoType | None] = Omitted()
    """Тип видео: обычное видео или видеосообщение"""
    width: Omittable[int | None] = Omitted()
    """Ширина видео"""

    @classmethod
    def factory(
        cls,
        url: str,
        token: str,
        thumbnail_url: Omittable[str] = Omitted(),
        width: Omittable[int | None] = Omitted(),
        height: Omittable[int | None] = Omitted(),
        duration: Omittable[int | None] = Omitted(),
    ) -> Self:
        """
        Фабричный метод.

        Args:
            url: URL медиа-вложения. Для видео-вложения используйте метод GetVideoAttachmentDetails, чтобы получить прямые ссылки.
            token: Используйте token, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении..
            thumbnail_url: URL изображения
            width: Ширина видео
            height: Высота видео
            duration: Длина видео в секундах
        """
        thumbnail: Omittable[VideoThumbnail]

        if is_not_omitted(thumbnail_url):
            thumbnail = VideoThumbnail(url=thumbnail_url)
        else:
            thumbnail = Omitted()

        return cls(
            payload=MediaAttachmentPayload(
                url=url,
                token=token,
            ),
            thumbnail=thumbnail,
            width=width,
            height=height,
            duration=duration,
        )

    @property
    def unsafe_duration(self) -> int:
        if is_defined(self.duration):
            return self.duration

        raise AttributeIsEmptyError(
            obj=self,
            attr="duration",
        )

    @property
    def unsafe_height(self) -> int:
        if is_defined(self.height):
            return self.height

        raise AttributeIsEmptyError(
            obj=self,
            attr="height",
        )

    @property
    def unsafe_thumbnail(self) -> VideoThumbnail:
        if is_defined(self.thumbnail):
            return self.thumbnail

        raise AttributeIsEmptyError(
            obj=self,
            attr="thumbnail",
        )

    @property
    def unsafe_video_type(self) -> VideoType:
        if is_defined(self.video_type):
            return self.video_type

        raise AttributeIsEmptyError(
            obj=self,
            attr="video_type",
        )

    @property
    def unsafe_width(self) -> int:
        if is_defined(self.width):
            return self.width

        raise AttributeIsEmptyError(
            obj=self,
            attr="width",
        )

    def to_request(self) -> VideoAttachmentRequest:
        return VideoAttachmentRequest.factory(token=self.payload.token)
