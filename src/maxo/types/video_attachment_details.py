from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.video_thumbnail import VideoThumbnail
from maxo.types.video_urls import VideoUrls


class VideoAttachmentDetails(MaxoType):
    """
    Args:
        duration: Длина видео в секундах
        height: Высота видео
        thumbnail: Миниатюра видео
        token: Токен видео-вложения
        urls: URL-ы для скачивания или воспроизведения видео. Может быть null, если видео недоступно
        width: Ширина видео
    """

    duration: int
    """Длина видео в секундах"""
    height: int
    """Высота видео"""
    token: str
    """Токен видео-вложения"""
    width: int
    """Ширина видео"""

    thumbnail: Omittable[VideoThumbnail | None] = Omitted()
    """Миниатюра видео"""
    urls: Omittable[VideoUrls | None] = Omitted()
    """URL-ы для скачивания или воспроизведения видео. Может быть null, если видео недоступно"""

    @property
    def unsafe_thumbnail(self) -> VideoThumbnail:
        if is_defined(self.thumbnail):
            return self.thumbnail

        raise AttributeIsEmptyError(
            obj=self,
            attr="thumbnail",
        )

    @property
    def unsafe_urls(self) -> VideoUrls:
        if is_defined(self.urls):
            return self.urls

        raise AttributeIsEmptyError(
            obj=self,
            attr="urls",
        )
