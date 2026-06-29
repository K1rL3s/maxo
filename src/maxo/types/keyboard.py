from maxo.types.base import MaxoType
from maxo.types.buttons import InlineButtons


class Keyboard(MaxoType):
    """
    Клавиатура - это двумерный массив кнопок. Подробнее о типах кнопок и клавиатуре в ботах - [в разделе «Клавиатура для чат-бота»](https://dev.max.ru/docs-api#Клавиатура%20для%20чат-бота)

    Args:
        buttons:
    """

    buttons: list[list[InlineButtons]]
