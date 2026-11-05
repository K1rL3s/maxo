from maxo.enums.markup_element_type import MarkupElementType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.markup_element import MarkupElement


class UserMentionMarkup(MarkupElement):
    """
    Представляет упоминание пользователя в тексте. Упоминание может быть как по имени пользователя, так и по ID, если у пользователя нет имени

    **Обратите внимание**: в тексте комментариев упоминание пользователя не поддерживаются

    Args:
        type:
        user_id: ID упомянутого пользователя без имени
        user_link: `@username` упомянутого пользователя
    """

    type: MarkupElementType = MarkupElementType.USER_MENTION

    user_id: Omittable[int | None] = Omitted()
    """ID упомянутого пользователя без имени"""
    user_link: Omittable[str | None] = Omitted()
    """`@username` упомянутого пользователя"""

    @property
    def unsafe_user_id(self) -> int:
        if is_defined(self.user_id):
            return self.user_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_id",
        )

    @property
    def unsafe_user_link(self) -> str:
        if is_defined(self.user_link):
            return self.user_link

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_link",
        )
