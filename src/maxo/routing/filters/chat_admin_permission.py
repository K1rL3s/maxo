from maxo.enums.chat_admin_permission import ChatAdminPermission
from maxo.omit import is_defined
from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.types.bot_admin_permissions_changed import BotAdminPermissionsChanged

_LEGACY_ALIASES = {
    ChatAdminPermission.EDIT_MESSAGE: ChatAdminPermission.EDIT,
    ChatAdminPermission.DELETE_MESSAGE: ChatAdminPermission.DELETE,
    ChatAdminPermission.POST_EDIT_DELETE_MESSAGE: ChatAdminPermission.WRITE,
}


class ChatAdminPermissionFilter(BaseFilter[BotAdminPermissionsChanged]):
    __slots__ = ("_permissions",)

    def __init__(self, *permissions: ChatAdminPermission) -> None:
        if not permissions:
            raise ValueError("At least one permission is required")
        self._permissions = frozenset(map(self._to_canon, permissions))

    def __str__(self) -> str:
        return self._signature_to_string(*sorted(self._permissions))

    async def __call__(self, update: BotAdminPermissionsChanged, ctx: Ctx) -> bool:
        if not update.is_admin or not is_defined(update.permissions):
            return False

        granted = {self._to_canon(granted) for granted in update.permissions}
        return self._permissions <= granted

    def _to_canon(self, permission: ChatAdminPermission) -> ChatAdminPermission:
        return _LEGACY_ALIASES.get(permission, permission)
