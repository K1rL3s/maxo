from maxo.types.base import MaxoType
from maxo.types.buttons import InlineButtons


class InlineKeyboardAttachmentRequestPayload(MaxoType):
    """
    Args:
        buttons: Двумерный массив кнопок. Подробнее о типах кнопок и клавиатуре в ботах - [в разделе «Клавиатура для чат-бота»](https://dev.max.ru/docs-api/use-cases/sending-messages/keyboard)
    """

    buttons: list[list[InlineButtons]]
    """Двумерный массив кнопок. Подробнее о типах кнопок и клавиатуре в ботах - [в разделе «Клавиатура для чат-бота»](https://dev.max.ru/docs-api/use-cases/sending-messages/keyboard)"""
