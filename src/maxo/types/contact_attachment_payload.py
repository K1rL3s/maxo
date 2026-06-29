from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.user import User


class ContactAttachmentPayload(MaxoType):
    """
    Args:
        hash: Хеш информации о пользователе в формате VCF. Используется для проверки того, что пользователь поделился номером телефона, привязанным к его аккаунту в МАКС<br/> Подробнее - [в разделе «Типы кнопок»](https://dev.max.ru/docs-api#Типы%20кнопок)
        max_info: Информация о пользователе
        vcf_info: Информация о пользователе в формате VCF
    """

    hash: Omittable[str | None] = Omitted()
    """Хеш информации о пользователе в формате VCF. Используется для проверки того, что пользователь поделился номером телефона, привязанным к его аккаунту в МАКС<br/> Подробнее - [в разделе «Типы кнопок»](https://dev.max.ru/docs-api#Типы%20кнопок)"""
    max_info: Omittable[User | None] = Omitted()
    """Информация о пользователе"""
    vcf_info: Omittable[str | None] = Omitted()
    """Информация о пользователе в формате VCF"""

    @property
    def unsafe_hash(self) -> str:
        if is_defined(self.hash):
            return self.hash

        raise AttributeIsEmptyError(
            obj=self,
            attr="hash",
        )

    @property
    def unsafe_max_info(self) -> User:
        if is_defined(self.max_info):
            return self.max_info

        raise AttributeIsEmptyError(
            obj=self,
            attr="max_info",
        )

    @property
    def unsafe_vcf_info(self) -> str:
        if is_defined(self.vcf_info):
            return self.vcf_info

        raise AttributeIsEmptyError(
            obj=self,
            attr="vcf_info",
        )
