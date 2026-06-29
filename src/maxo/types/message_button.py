from maxo.enums.button_type import ButtonType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.button import Button


class MessageButton(Button):
    """
    Кнопка для запуска мини-приложения

    Args:
        text: Текст кнопки, который будет отправлен в чат от лица пользователя
        type:
    """

    type: ButtonType = ButtonType.MESSAGE

    text: Omittable[str] = Omitted()  # type: ignore[assignment]
    """Текст кнопки, который будет отправлен в чат от лица пользователя"""

    @property
    def unsafe_text(self) -> str:
        if is_defined(self.text):
            return self.text

        raise AttributeIsEmptyError(
            obj=self,
            attr="text",
        )
