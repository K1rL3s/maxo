"""Тесты MessageManager - закрывают п.1 issue #110 (skip get_message_by_id в remove_inline_kbd)."""

from unittest.mock import AsyncMock

from maxo.dialogs.api.entities import OldMessage, ShowMode
from maxo.dialogs.manager.message_manager import MessageManager
from maxo.enums import ChatType
from maxo.types import InlineKeyboardAttachment, Recipient


def _make_old_message_with_kbd(mid: str = "55") -> OldMessage:
    return OldMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        message_id=mid,
        sequence_id=int(mid),
        text="x",
        attachments=[InlineKeyboardAttachment.factory(buttons=[])],
    )


async def test_remove_inline_kbd_skips_refetch() -> None:
    """remove_inline_kbd не делает get_message_by_id после edit."""
    bot = AsyncMock()
    bot.edit_message = AsyncMock()
    bot.get_message_by_id = AsyncMock()
    mgr = MessageManager(media_id_storage=AsyncMock())

    result = await mgr.remove_inline_kbd(bot, _make_old_message_with_kbd(mid="55"))  # type: ignore[func-returns-value]

    bot.edit_message.assert_awaited_once()
    bot.get_message_by_id.assert_not_called()
    assert result is None


async def test_remove_kbd_no_update_returns_none() -> None:
    """remove_kbd с ShowMode.NO_UPDATE возвращает None."""
    mgr = MessageManager(media_id_storage=AsyncMock())
    result = await mgr.remove_kbd(  # type: ignore[func-returns-value]
        bot=AsyncMock(),
        show_mode=ShowMode.NO_UPDATE,
        old_message=None,
    )
    assert result is None
