from datetime import datetime

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class User(MaxoType):
    """
    Объект, описывающий один из вариантов наследования:

    - [`User`](https://dev.max.ru/docs-api/objects/User) - объект содержит общую информацию о пользователе или боте без аватара
    - [`UserWithPhoto`](https://dev.max.ru/docs-api/objects/UserWithPhoto) - объект с общей информацией о пользователе или боте, дополнительно содержит URL аватара и описание
    - [`BotInfo`](https://dev.max.ru/docs-api/objects/BotInfo) - объект включает общую информацию о боте, URL аватара и описание. Дополнительно содержит список команд, поддерживаемых ботом. Возвращается только при вызове метода [`GET /me`](https://dev.max.ru/docs-api/methods/GET/me)
    - [`ChatMember`](https://dev.max.ru/docs-api/objects/ChatMember) - объект включает общую информацию о пользователе или боте, URL аватара и описание при его наличии. Дополнительно содержит данные для пользователей-участников чата. Возвращается только при вызове некоторых методов группы `/chats`, например [`GET /chats/{chatId}/members`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members)

    Args:
        first_name: Отображаемое имя пользователя или бота
        is_bot: `true`, если это бот
        last_activity_time: Время последней активности пользователя или бота в MAX (Unix-время в миллисекундах). Если пользователь отключил в настройках профиля мессенджера MAX возможность видеть, что он в сети онлайн, поле может не возвращаться
        last_name: Отображаемая фамилия пользователя. Для ботов это поле не возвращается
        name: _Устаревшее поле, скоро будет удалено_
        user_id: Идентификатор пользователя или бота
        username: Никнейм бота или уникальное публичное имя пользователя. В случае с пользователем может быть `null`, если тот недоступен или имя не задано
    """

    first_name: str
    """Отображаемое имя пользователя или бота"""
    is_bot: bool
    """`true`, если это бот"""
    last_activity_time: datetime
    """Время последней активности пользователя или бота в MAX (Unix-время в миллисекундах). Если пользователь отключил в настройках профиля мессенджера MAX возможность видеть, что он в сети онлайн, поле может не возвращаться"""
    user_id: int
    """Идентификатор пользователя или бота"""

    username: str | None = None
    """Никнейм бота или уникальное публичное имя пользователя. В случае с пользователем может быть `null`, если тот недоступен или имя не задано"""

    last_name: Omittable[str | None] = Omitted()
    """Отображаемая фамилия пользователя. Для ботов это поле не возвращается"""
    name: Omittable[str | None] = Omitted()
    """_Устаревшее поле, скоро будет удалено_"""

    @property
    def id(self) -> int:
        return self.user_id

    @property
    def fullname(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    full_name = fullname  # Подражание aiogram

    @property
    def unsafe_last_name(self) -> str:
        if is_defined(self.last_name):
            return self.last_name

        raise AttributeIsEmptyError(
            obj=self,
            attr="last_name",
        )

    @property
    def unsafe_name(self) -> str:
        if is_defined(self.name):
            return self.name

        raise AttributeIsEmptyError(
            obj=self,
            attr="name",
        )

    @property
    def unsafe_username(self) -> str:
        if is_defined(self.username):
            return self.username

        raise AttributeIsEmptyError(
            obj=self,
            attr="username",
        )
