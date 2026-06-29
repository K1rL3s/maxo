from typing import Self

from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.omit import Omittable, Omitted
from maxo.types.attachment_request import AttachmentRequest
from maxo.types.contact_attachment_request_payload import (
    ContactAttachmentRequestPayload,
)


class ContactAttachmentRequest(AttachmentRequest):
    """
    Запрос на прикрепление карточки контакта к сообщению. Должен быть единственным вложением в сообщении

    Args:
        payload:
        type:
    """

    type: AttachmentRequestType = AttachmentRequestType.CONTACT

    payload: ContactAttachmentRequestPayload

    @classmethod
    def factory(
        cls,
        name: str | None = None,
        contact_id: Omittable[int | None] = Omitted(),
        vcf_info: Omittable[str | None] = Omitted(),
        vcf_phone: Omittable[str | None] = Omitted(),
    ) -> Self:
        """
        Фабричный метод.

        Args:
            name: Имя контакта.
            contact_id: ID контакта, если он зарегистирован в MAX.
            vcf_info: Полная информация о контакте в формате VCF.
            vcf_phone: Телефон контакта в формате VCF.

        """
        return cls(
            payload=ContactAttachmentRequestPayload(
                name=name,
                contact_id=contact_id,
                vcf_info=vcf_info,
                vcf_phone=vcf_phone,
            ),
        )
