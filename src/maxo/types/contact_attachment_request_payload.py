from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class ContactAttachmentRequestPayload(MaxoType):
    """
    Args:
        contact_id: ID контакта, если он зарегистрирован в MAX
        name: Имя контакта
        vcf_info: Полная информация о контакте в формате VCF
        vcf_phone: Телефон контакта в формате VCF
    """

    name: str | None = None
    """Имя контакта"""

    contact_id: Omittable[int | None] = Omitted()
    """ID контакта, если он зарегистрирован в MAX"""
    vcf_info: Omittable[str | None] = Omitted()
    """Полная информация о контакте в формате VCF"""
    vcf_phone: Omittable[str | None] = Omitted()
    """Телефон контакта в формате VCF"""

    @property
    def unsafe_contact_id(self) -> int:
        if is_defined(self.contact_id):
            return self.contact_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="contact_id",
        )

    @property
    def unsafe_name(self) -> str:
        if is_defined(self.name):
            return self.name

        raise AttributeIsEmptyError(
            obj=self,
            attr="name",
        )

    @property
    def unsafe_vcf_info(self) -> str:
        if is_defined(self.vcf_info):
            return self.vcf_info

        raise AttributeIsEmptyError(
            obj=self,
            attr="vcf_info",
        )

    @property
    def unsafe_vcf_phone(self) -> str:
        if is_defined(self.vcf_phone):
            return self.vcf_phone

        raise AttributeIsEmptyError(
            obj=self,
            attr="vcf_phone",
        )
