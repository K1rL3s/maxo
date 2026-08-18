from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class ShareAttachmentPayload(MaxoType):
    """
    Данные прикреплённого к сообщению предпросмотра медиавложения

    Args:
        token: Токен вложения
        url: URL, прикреплённый к сообщению для предпросмотра медиавложения
    """

    token: Omittable[str | None] = Omitted()
    """Токен вложения"""
    url: Omittable[str | None] = Omitted()
    """URL, прикреплённый к сообщению для предпросмотра медиавложения"""

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
