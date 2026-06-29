from datetime import datetime

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.user import User


class Callback(MaxoType):
    """
    Объект, отправленный боту, когда пользователь нажимает кнопку

    Args:
        callback_id: Текущий ID клавиатуры
        payload: Токен кнопки
        timestamp: Unix-время, когда пользователь нажал кнопку
        user: Пользователь, нажавший на кнопку
    """

    callback_id: str
    """Текущий ID клавиатуры"""
    timestamp: datetime
    """Unix-время, когда пользователь нажал кнопку"""
    user: User
    """Пользователь, нажавший на кнопку"""

    payload: Omittable[str] = Omitted()
    """Токен кнопки"""

    @property
    def id(self) -> str:
        return self.callback_id

    @property
    def unsafe_payload(self) -> str:
        if is_defined(self.payload):
            return self.payload

        raise AttributeIsEmptyError(
            obj=self,
            attr="payload",
        )

    # Подражание aiogram
    @property
    def data(self) -> Omittable[str]:
        return self.payload

    unsafe_data = unsafe_payload  # Подражание aiogram
