from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.buttons import InlineButtons
from maxo.types.inline_keyboard_attachment_request_payload import (
    InlineKeyboardAttachmentRequestPayload,
)


class InlineKeyboardAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление клавиатуры к сообщению

    Args:
        payload: Данные для прикрепления кнопок к сообщению
            Ограничения:
            - Максимальное количество кнопок в ряду - 7
            - Максимальное количество строк с кнопками - 30
            - Если в ряду кнопки с типами: `link`, `open_app`, `request_geo_location`, `request_contact`, то максимальное количество кнопок в ряду - 3
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.INLINE_KEYBOARD

    payload: InlineKeyboardAttachmentRequestPayload
    """
    Данные для прикрепления кнопок к сообщению
    Ограничения:
        - Максимальное количество кнопок в ряду - 7
        - Максимальное количество строк с кнопками - 30
        - Если в ряду кнопки с типами: `link`, `open_app`, `request_geo_location`, `request_contact`, то максимальное количество кнопок в ряду - 3
    """

    @classmethod
    def factory(
        cls,
        buttons: list[list[InlineButtons]],
    ) -> Self:
        return cls(
            payload=InlineKeyboardAttachmentRequestPayload(
                buttons=buttons,
            ),
        )
