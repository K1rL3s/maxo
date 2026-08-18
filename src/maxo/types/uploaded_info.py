from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class UploadedInfo(MaxoType):
    """
    Данные, которые вы получили в ответ на запрос [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads). Можно передавать после того, как вы загрузили аудио, видео или файл и получили в ответ от сервера `retval`. Подробнее - в описании [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads)

    Args:
        token: Токен вложения - уникальный ID загруженного медиа: изображения, аудио, видео или файла. Возвращается в ответ на вызов [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads)
    """

    token: Omittable[str] = Omitted()
    """Токен вложения - уникальный ID загруженного медиа: изображения, аудио, видео или файла. Возвращается в ответ на вызов [POST /uploads](https://dev.max.ru/docs-api/methods/POST/uploads)"""

    @property
    def unsafe_token(self) -> str:
        if is_defined(self.token):
            return self.token

        raise AttributeIsEmptyError(
            obj=self,
            attr="token",
        )
