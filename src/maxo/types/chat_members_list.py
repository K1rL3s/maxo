from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.chat_member import ChatMember


class ChatMembersList(MaxoType):
    """
    Args:
        marker: Указатель на следующую страницу данных
        members: Список участников группового чата или канала с общей информацией о них, а также временем последней активности и списком прав доступа для пользователей и ботов, которые являются администраторами
    """

    members: list[ChatMember]
    """Список участников группового чата или канала с общей информацией о них, а также временем последней активности и списком прав доступа для пользователей и ботов, которые являются администраторами"""

    marker: Omittable[int | None] = Omitted()
    """Указатель на следующую страницу данных"""

    @property
    def unsafe_marker(self) -> int:
        if is_defined(self.marker):
            return self.marker

        raise AttributeIsEmptyError(
            obj=self,
            attr="marker",
        )
