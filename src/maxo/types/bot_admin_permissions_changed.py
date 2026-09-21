from maxo.enums.chat_admin_permission import ChatAdminPermission
from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade


class BotAdminPermissionsChanged(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие при изменении прав администратора группового чата или канала

    Args:
        bot_id: Идентификатор бота, чьи права администратора были изменены
        chat_id: Идентификатор группового чата или канала, в котором произошло событие
        is_admin: Признак того, является ли бот администратором канала или группового чата или нет
        is_channel: Признак того, что событие произошло в канале
        permissions:
        type:
        user_id: Идентификатор пользователя или бота, который изменил права администратора
    """

    type = UpdateType.BOT_ADMIN_PERMISSIONS_CHANGED

    bot_id: int
    """Идентификатор бота, чьи права администратора были изменены"""
    chat_id: int
    """Идентификатор группового чата или канала, в котором произошло событие"""
    is_admin: bool
    """Признак того, является ли бот администратором канала или группового чата или нет"""
    is_channel: bool
    """Признак того, что событие произошло в канале"""
    user_id: int
    """Идентификатор пользователя или бота, который изменил права администратора"""

    permissions: Omittable[list[ChatAdminPermission] | None] = Omitted()

    @property
    def unsafe_permissions(self) -> list[ChatAdminPermission]:
        if is_defined(self.permissions):
            return self.permissions

        raise AttributeIsEmptyError(
            obj=self,
            attr="permissions",
        )
