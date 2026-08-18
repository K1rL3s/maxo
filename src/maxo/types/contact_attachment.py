from typing import Self

from maxo.enums.attachment_type import AttachmentType
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachment import Attachment
from maxo.types.contact_attachment_payload import ContactAttachmentPayload
from maxo.types.contact_attachment_request import ContactAttachmentRequest
from maxo.types.user import User


class ContactAttachment(Attachment):
    """
    Args:
        payload: Результат загрузки данных контакта в сообщение
        type:
    """

    type: AttachmentType = AttachmentType.CONTACT

    payload: ContactAttachmentPayload
    """Результат загрузки данных контакта в сообщение"""

    @classmethod
    def factory(
        cls,
        vcf_info: Omittable[str | None] = Omitted(),
        max_info: Omittable[User | None] = Omitted(),
    ) -> Self:
        """
        Фабричный метод.

        Args:
            vcf_info: Информация о пользователе в формате VCF.
            max_info: Информация о пользователе.

        """
        return cls(
            payload=ContactAttachmentPayload(
                max_info=max_info,
                vcf_info=vcf_info,
            ),
        )

    def to_request(self) -> ContactAttachmentRequest:
        return ContactAttachmentRequest.factory(
            name=(
                self.payload.max_info.first_name
                if is_defined(self.payload.max_info)
                else None
            ),
            contact_id=(
                self.payload.max_info.user_id
                if is_defined(self.payload.max_info)
                else Omitted()
            ),
            vcf_info=self.payload.vcf_info,
        )
