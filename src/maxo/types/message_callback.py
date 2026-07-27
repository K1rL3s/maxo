from typing import TypeAlias

from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins.callback import CallbackMethodsFacade
from maxo.routing.mixins.message import MessageMethodsFacade
from maxo.types.base import MaxUpdate
from maxo.types.callback import Callback
from maxo.types.message import Message
from maxo.types.user import User


class MessageCallback(MaxUpdate, CallbackMethodsFacade, MessageMethodsFacade):  # type: ignore[misc]
    """
    Вы получите это событие, как только пользователь нажмёт кнопку

    Args:
        callback:
        message: Изначальное сообщение, содержащее встроенную клавиатуру. Может быть `null`, если оно было удалено к моменту, когда бот получил это событие
        type:
        user_locale: Текущий язык пользователя в формате IETF BCP 47
    """

    type = UpdateType.MESSAGE_CALLBACK

    callback: Callback

    message: Message | None = None
    """Изначальное сообщение, содержащее встроенную клавиатуру. Может быть `null`, если оно было удалено к моменту, когда бот получил это событие"""

    user_locale: Omittable[str | None] = Omitted()
    """Текущий язык пользователя в формате IETF BCP 47"""

    @property
    def unsafe_message(self) -> Message:
        if is_defined(self.message):
            return self.message

        raise AttributeIsEmptyError(
            obj=self,
            attr="message",
        )

    @property
    def unsafe_user_locale(self) -> str:
        if is_defined(self.user_locale):
            return self.user_locale

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_locale",
        )

    @property
    def callback_id(self) -> str:
        return self.callback.callback_id

    id = callback_id

    @property
    def payload(self) -> Omittable[str]:
        return self.callback.payload

    data = payload  # Подражание aiogram

    @property
    def user(self) -> User:
        return self.callback.user

    from_user = user  # Подражание aiogram


CallbackQuery: TypeAlias = MessageCallback  # Подражание aiogram
