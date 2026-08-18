from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.attachment_request import AttachmentRequest


class LocationAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление геолокации к сообщению

    Args:
        latitude: Широта, до 15 символов
        longitude: Долгота, до 15 символов
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.LOCATION

    latitude: float
    """Широта, до 15 символов"""
    longitude: float
    """Долгота, до 15 символов"""
