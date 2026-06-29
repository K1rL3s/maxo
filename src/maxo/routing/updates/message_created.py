from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins import MessageMethodsFacade
from maxo.routing.updates.base import MaxUpdate
from maxo.types.message import Message


class MessageCreated(MaxUpdate, MessageMethodsFacade):
    """
    Вы получите это событие, как только сообщение будет создано

    Args:
        message: Новое созданное сообщение
        type:
        user_locale: Текущий язык пользователя в формате IETF BCP 47. Доступно только в диалогах
    """

    type = UpdateType.MESSAGE_CREATED

    message: Message
    """Новое созданное сообщение"""

    user_locale: Omittable[str | None] = Omitted()
    """Текущий язык пользователя в формате IETF BCP 47. Доступно только в диалогах"""

    @property
    def unsafe_user_locale(self) -> str:
        if is_defined(self.user_locale):
            return self.user_locale

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_locale",
        )

    @property
    def text(self) -> str | None:
        return self.message.body.text

    @property
    def user_id(self) -> int | None:
        if is_defined(self.message.sender):
            return self.message.sender.user_id
        return None
