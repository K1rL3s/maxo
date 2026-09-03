from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades import ChatMethodsFacade
from maxo.types.user import User


class BotStopped(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь остановит бота в его настройках в МАКС

    Args:
        chat_id: ID диалога, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        type:
        user: Пользователь, который остановил бота
        user_locale: Текущий язык пользователя в формате IETF BCP 47
    """

    type = UpdateType.BOT_STOPPED

    chat_id: int
    """ID диалога, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    user: User
    """Пользователь, который остановил бота"""

    user_locale: Omittable[str] = Omitted()
    """Текущий язык пользователя в формате IETF BCP 47"""

    @property
    def unsafe_user_locale(self) -> str:
        if is_defined(self.user_locale):
            return self.user_locale

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_locale",
        )
