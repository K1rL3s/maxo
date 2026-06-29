from maxo.enums.button_type import ButtonType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.button import Button


class OpenAppButton(Button):
    """
    Кнопка для запуска мини-приложения

    Args:
        contact_id: Идентификатор бота, чьё мини-приложение надо запустить
        payload: Параметр запуска, который будет передан в [initData](https://dev.max.ru/docs/webapps/bridge#WebAppData) мини-приложения
        type:
        web_app: Публичное имя (username) бота или ссылка на него, чьё мини-приложение надо запустить
    """

    type: ButtonType = ButtonType.OPEN_APP

    contact_id: Omittable[int] = Omitted()
    """Идентификатор бота, чьё мини-приложение надо запустить"""
    payload: Omittable[str] = Omitted()
    """Параметр запуска, который будет передан в [initData](https://dev.max.ru/docs/webapps/bridge#WebAppData) мини-приложения"""
    web_app: Omittable[str] = Omitted()
    """Публичное имя (username) бота или ссылка на него, чьё мини-приложение надо запустить"""

    @property
    def unsafe_contact_id(self) -> int:
        if is_defined(self.contact_id):
            return self.contact_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="contact_id",
        )

    @property
    def unsafe_payload(self) -> str:
        if is_defined(self.payload):
            return self.payload

        raise AttributeIsEmptyError(
            obj=self,
            attr="payload",
        )

    @property
    def unsafe_web_app(self) -> str:
        if is_defined(self.web_app):
            return self.web_app

        raise AttributeIsEmptyError(
            obj=self,
            attr="web_app",
        )
