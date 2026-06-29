from maxo.enums.button_type import ButtonType
from maxo.types.button import Button


class RequestContactButton(Button):
    """
    После нажатия на такую кнопку клиент отправляет новое сообщение с вложением текущего контакта пользователя

    Args:
        type:
    """

    type: ButtonType = ButtonType.REQUEST_CONTACT
