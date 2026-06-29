from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins import ChatMethodsFacade
from maxo.routing.updates.base import MaxUpdate
from maxo.types.user import User


class UserAddedToChat(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь будет добавлен в чат, где бот является администратором

    Args:
        chat_id: ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        inviter_id: Пользователь, который добавил нового пользователя в чат. Может быть `null`, если пользователь присоединился к чату по ссылке
        is_channel: Указывает, что пользователь добавлен в канал, а не в чат
        type:
        user: Пользователь, добавленный в чат
    """

    type = UpdateType.USER_ADDED

    chat_id: int
    """ID чата, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    is_channel: bool
    """Указывает, что пользователь добавлен в канал, а не в чат"""
    user: User
    """Пользователь, добавленный в чат"""

    inviter_id: Omittable[int | None] = Omitted()
    """Пользователь, который добавил нового пользователя в чат. Может быть `null`, если пользователь присоединился к чату по ссылке"""

    @property
    def unsafe_inviter_id(self) -> int:
        if is_defined(self.inviter_id):
            return self.inviter_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="inviter_id",
        )
