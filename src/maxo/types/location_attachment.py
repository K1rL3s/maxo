from maxo.enums.attachment_type import AttachmentType
from maxo.types.attachment import Attachment
from maxo.types.location_attachment_request import LocationAttachmentRequest


class LocationAttachment(Attachment):
    """
    Args:
        latitude: Широта, до 15 символов
        longitude: Долгота, до 15 символов
        type:
    """

    type: AttachmentType = AttachmentType.LOCATION

    latitude: float
    """Широта, до 15 символов"""
    longitude: float
    """Долгота, до 15 символов"""

    def to_request(self) -> LocationAttachmentRequest:
        return LocationAttachmentRequest(
            latitude=self.latitude,
            longitude=self.longitude,
        )
