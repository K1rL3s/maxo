from maxo.enums.button_type import ButtonType
from maxo.types.button import Button


class ClipboardButton(Button):
    """
    При нажатии на кнопку с типом `clipboard` текст, указанный в свойстве `payload`, копируется в буфер обмена

    Args:
        payload: Текст, который будет скопирован
        type:
    """

    type: ButtonType = ButtonType.CLIPBOARD

    payload: str
    """Текст, который будет скопирован"""
