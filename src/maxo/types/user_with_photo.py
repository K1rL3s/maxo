from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.user import User


class UserWithPhoto(User):
    """
    Объект с общей информацией о пользователе или боте. Является наследником [схемы User](https://dev.max.ru/docs-api/objects/User) - дополнительно к ней содержит URL аватара и описание

    Args:
        avatar_url: URL аватара пользователя или бота в уменьшенном размере
        description: Описание пользователя или бота. В случае с пользователем может принимать значение `null`, если описание не заполнено
        full_avatar_url: URL аватара пользователя или бота в полном размере
    """

    avatar_url: Omittable[str] = Omitted()
    """URL аватара пользователя или бота в уменьшенном размере"""
    description: Omittable[str | None] = Omitted()
    """Описание пользователя или бота. В случае с пользователем может принимать значение `null`, если описание не заполнено"""
    full_avatar_url: Omittable[str] = Omitted()
    """URL аватара пользователя или бота в полном размере"""

    @property
    def unsafe_avatar_url(self) -> str:
        if is_defined(self.avatar_url):
            return self.avatar_url

        raise AttributeIsEmptyError(
            obj=self,
            attr="avatar_url",
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
    def unsafe_full_avatar_url(self) -> str:
        if is_defined(self.full_avatar_url):
            return self.full_avatar_url

        raise AttributeIsEmptyError(
            obj=self,
            attr="full_avatar_url",
        )
