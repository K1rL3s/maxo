from datetime import UTC, datetime
from unittest.mock import AsyncMock

from maxo.bot import Bot
from maxo.enums import ChatStatus, ChatType
from maxo.types.chat import Chat
from maxo.types.chat_list import ChatList
from maxo.utils.iterators.chats import ChatsIterator

TOKEN = "f9LHod"  # noqa: S105


def create_chat(chat_id: int) -> Chat:
    return Chat(
        chat_id=chat_id,
        type=ChatType.PRIVATE,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=2,
        status=ChatStatus.ACTIVE,
    )


async def test_chats_iterator_single_page():
    bot = Bot(token=TOKEN)
    bot.get_chats = AsyncMock(
        side_effect=[
            ChatList(chats=[create_chat(1), create_chat(2)], marker=None),
            ChatList(chats=[], marker=None),
        ],
    )

    iterator = ChatsIterator(bot=bot)
    chats = [chat async for chat in iterator]

    assert len(chats) == 2
    assert chats[0].chat_id == 1
    assert chats[1].chat_id == 2
    assert bot.get_chats.await_count == 2


async def test_chats_iterator_multiple_pages():
    bot = Bot(token=TOKEN)
    bot.get_chats = AsyncMock(
        side_effect=[
            ChatList(chats=[create_chat(1), create_chat(2)], marker=123),
            ChatList(chats=[create_chat(3), create_chat(4)], marker=None),
            ChatList(chats=[], marker=None),
        ],
    )

    iterator = ChatsIterator(bot=bot)
    chats = [chat async for chat in iterator]

    assert len(chats) == 4
    assert chats[0].chat_id == 1
    assert chats[1].chat_id == 2
    assert chats[2].chat_id == 3
    assert chats[3].chat_id == 4
    assert bot.get_chats.await_count == 3


async def test_chats_iterator_no_chats():
    bot = Bot(token=TOKEN)
    bot.get_chats = AsyncMock(return_value=ChatList(chats=[], marker=None))

    iterator = ChatsIterator(bot=bot)
    chats = [chat async for chat in iterator]

    assert len(chats) == 0
    bot.get_chats.assert_awaited_once()
