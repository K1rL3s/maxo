from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class UploadEndpoint(MaxoType):
    """
    Точка доступа, куда следует загружать ваши бинарные файлы

    Args:
        token: Токен для отправки медиафайла во вложении к сообщению с помощью [POST /messages](https://dev.max.ru/docs-api/methods/POST/messages) или [PUT /messages](https://dev.max.ru/docs-api/methods/PUT/messages)
        url: URL для загрузки медиафайла. Срок жизни ссылки не ограничен
    """

    url: str
    """URL для загрузки медиафайла. Срок жизни ссылки не ограничен"""

    token: Omittable[str | None] = Omitted()
    """Токен для отправки медиафайла во вложении к сообщению с помощью [POST /messages](https://dev.max.ru/docs-api/methods/POST/messages) или [PUT /messages](https://dev.max.ru/docs-api/methods/PUT/messages)"""

    @property
    def unsafe_token(self) -> str:
        if is_defined(self.token):
            return self.token

        raise AttributeIsEmptyError(
            obj=self,
            attr="token",
        )
