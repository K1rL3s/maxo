from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class UploadedInfo(MaxoType):
    """
    Это информация, которую вы получите, как только аудио/видео будет загружено

    Args:
        token: Токен - уникальный ID загруженного медиафайла
    """

    token: Omittable[str] = Omitted()
    """Токен - уникальный ID загруженного медиафайла"""

    @property
    def unsafe_token(self) -> str:
        if is_defined(self.token):
            return self.token

        raise AttributeIsEmptyError(
            obj=self,
            attr="token",
        )
