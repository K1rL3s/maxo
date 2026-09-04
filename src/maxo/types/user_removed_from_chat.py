from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.user import User


class UserRemovedFromChat(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь будет удалён из чата, где бот является администратором

    Args:
        admin_id: Администратор, который удалил пользователя из чата. Может быть `null`, если пользователь покинул чат сам
        chat_id: ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        is_channel: Указывает, что пользователь удалён из канала, а не из чата
        type:
        user: Пользователь, удалённый из чата
    """

    type = UpdateType.USER_REMOVED

    chat_id: int
    """ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    is_channel: bool
    """Указывает, что пользователь удалён из канала, а не из чата"""
    user: User
    """Пользователь, удалённый из чата"""

    admin_id: Omittable[int] = Omitted()
    """Администратор, который удалил пользователя из чата. Может быть `null`, если пользователь покинул чат сам"""

    @property
    def unsafe_admin_id(self) -> int:
        if is_defined(self.admin_id):
            return self.admin_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="admin_id",
        )
