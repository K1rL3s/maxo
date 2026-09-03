from datetime import datetime

from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades import ChatMethodsFacade
from maxo.types.user import User


class DialogMuted(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь отключит уведомления о новых сообщениях в диалоге с ботом

    Args:
        chat_id: ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        muted_until: Время в формате Unix timestamp в миллисекундах, до наступления которого диалог был отключён
        type:
        user: Пользователь, который отключил уведомления
        user_locale: Текущий язык пользователя в формате IETF BCP 47
    """

    type = UpdateType.DIALOG_MUTED

    chat_id: int
    """ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    muted_until: datetime
    """Время в формате Unix timestamp в миллисекундах, до наступления которого диалог был отключён"""
    user: User
    """Пользователь, который отключил уведомления"""

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
