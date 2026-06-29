from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.chat_admin import ChatAdmin


class ChatAdminsList(MaxoType):
    """
    Args:
        admins: Список пользователей и ботов, которые получат права администратора группового чата или канала
        marker: Указатель на следующую страницу данных
    """

    admins: list[ChatAdmin]
    """Список пользователей и ботов, которые получат права администратора группового чата или канала"""

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
