from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.user import User


class DialogCleared(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь очистит историю сообщений

    Args:
        chat_id: ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        type:
        user: Пользователь, который очистил историю сообщений
        user_locale: Текущий язык пользователя в формате IETF BCP 47
    """

    type = UpdateType.DIALOG_CLEARED

    chat_id: int
    """ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    user: User
    """Пользователь, который очистил историю сообщений"""

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
