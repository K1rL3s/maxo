from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.photo_token import PhotoToken


class PhotoAttachmentRequestPayload(MaxoType):
    """
    Данные для прикрепления изображения (все поля являются взаимоисключающими). Вместе с изображениями можно прикрепить видеофайлы (`type: video`) и одно вложение с кнопками (`type: inline_keyboard`). Общее количество вложений не должно превышать общее ограничение - 12. Подробнее - [в примерах](https://dev.max.ru/docs-api#Примеры%20с%20видео,%20изображением,%20файлом)

    Args:
        photos: Токены, полученные после загрузки изображений
        token: Токен существующего вложения
        url: Любой внешний URL изображения, которое вы хотите прикрепить
    """

    photos: Omittable[list[PhotoToken] | None] = Omitted()  # TODO: Проверить кто это
    """Токены, полученные после загрузки изображений"""
    token: Omittable[str | None] = Omitted()
    """Токен существующего вложения"""
    url: Omittable[str | None] = Omitted()
    """Любой внешний URL изображения, которое вы хотите прикрепить"""

    @property
    def unsafe_photos(self) -> list[PhotoToken]:
        if is_defined(self.photos):
            return self.photos

        raise AttributeIsEmptyError(
            obj=self,
            attr="photos",
        )

    @property
    def unsafe_token(self) -> str:
        if is_defined(self.token):
            return self.token

        raise AttributeIsEmptyError(
            obj=self,
            attr="token",
        )

    @property
    def unsafe_url(self) -> str:
        if is_defined(self.url):
            return self.url

        raise AttributeIsEmptyError(
            obj=self,
            attr="url",
        )
