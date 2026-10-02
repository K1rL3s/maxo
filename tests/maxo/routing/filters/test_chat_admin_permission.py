import pytest

from maxo import Ctx
from maxo.enums import ChatAdminPermission
from maxo.omit import Omittable, Omitted
from maxo.routing.filters.chat_admin_permission import ChatAdminPermissionFilter
from maxo.types import BotAdminPermissionsChanged
from tests.constants import BOT_ID, NOW


def make_update(
    permissions: Omittable[list[ChatAdminPermission] | None] = Omitted(),
    *,
    is_admin: bool = True,
) -> BotAdminPermissionsChanged:
    return BotAdminPermissionsChanged(
        bot_id=BOT_ID,
        chat_id=-1,
        user_id=2,
        is_admin=is_admin,
        is_channel=False,
        permissions=permissions,
        timestamp=NOW,
    )


async def test_passes_when_every_permission_granted() -> None:
    permission_filter = ChatAdminPermissionFilter(
        ChatAdminPermission.WRITE,
        ChatAdminPermission.PIN_MESSAGE,
    )
    update = make_update(
        [
            ChatAdminPermission.PIN_MESSAGE,
            ChatAdminPermission.READ_ALL_MESSAGES,
            ChatAdminPermission.WRITE,
        ],
    )

    assert await permission_filter(update, Ctx({})) is True


async def test_fails_when_one_permission_missing() -> None:
    permission_filter = ChatAdminPermissionFilter(
        ChatAdminPermission.WRITE,
        ChatAdminPermission.PIN_MESSAGE,
    )
    update = make_update([ChatAdminPermission.WRITE])

    assert await permission_filter(update, Ctx({})) is False


async def test_legacy_permission_in_update_counts_as_current() -> None:
    permission_filter = ChatAdminPermissionFilter(
        ChatAdminPermission.WRITE,
        ChatAdminPermission.EDIT,
        ChatAdminPermission.DELETE,
    )
    update = make_update(
        [
            ChatAdminPermission.POST_EDIT_DELETE_MESSAGE,
            ChatAdminPermission.EDIT_MESSAGE,
            ChatAdminPermission.DELETE_MESSAGE,
        ],
    )

    assert await permission_filter(update, Ctx({})) is True


async def test_legacy_permission_in_filter_counts_as_current() -> None:
    permission_filter = ChatAdminPermissionFilter(ChatAdminPermission.EDIT_MESSAGE)
    update = make_update([ChatAdminPermission.EDIT])

    assert await permission_filter(update, Ctx({})) is True


async def test_fails_on_demoted_bot() -> None:
    permission_filter = ChatAdminPermissionFilter(ChatAdminPermission.WRITE)

    assert await permission_filter(make_update(is_admin=False), Ctx({})) is False
    assert await permission_filter(make_update(None), Ctx({})) is False
    assert await permission_filter(make_update([]), Ctx({})) is False


async def test_any_permission_through_or_operator() -> None:
    permission_filter = ChatAdminPermissionFilter(
        ChatAdminPermission.WRITE,
    ) | ChatAdminPermissionFilter(ChatAdminPermission.VIEW_STATS)
    update = make_update([ChatAdminPermission.VIEW_STATS])

    assert await permission_filter(update, Ctx({})) is True


def test_requires_permissions() -> None:
    with pytest.raises(ValueError, match="At least one permission is required"):
        ChatAdminPermissionFilter()


def test_signature_keeps_canonical_permissions() -> None:
    permission_filter = ChatAdminPermissionFilter(ChatAdminPermission.EDIT_MESSAGE)

    assert str(permission_filter) == (
        "ChatAdminPermissionFilter(<ChatAdminPermission.EDIT: 'edit'>)"
    )
