from unittest.mock import ANY, AsyncMock

import pytest

from maxo.bot import Bot
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.types.chat_member import ChatMember
from maxo.types.chat_members_list import ChatMembersList
from maxo.utils.iterators.chat_members import ChatMembersIterator
from tests.constants import NOW


@pytest.fixture
def bot() -> Bot:
    return FakeBot()


def create_chat_member(user_id: int) -> ChatMember:
    return ChatMember(
        user_id=user_id,
        is_admin=False,
        first_name=f"Test{user_id}",
        is_bot=False,
        last_activity_time=NOW,
        is_owner=False,
        join_time=NOW,
        last_access_time=NOW,
    )


async def test_chat_members_iterator_single_page(bot: Bot) -> None:
    bot.get_members = AsyncMock(
        side_effect=[
            ChatMembersList(
                members=[create_chat_member(1), create_chat_member(2)],
                marker=None,
            ),
        ],
    )

    iterator = ChatMembersIterator(bot=bot, chat_id=1)
    members = [member async for member in iterator]

    assert len(members) == 2
    assert members[0].user_id == 1
    assert members[1].user_id == 2
    assert bot.get_members.await_count == 1


async def test_chat_members_iterator_multiple_pages(bot: Bot) -> None:
    bot.get_members = AsyncMock(
        side_effect=[
            ChatMembersList(
                members=[create_chat_member(1), create_chat_member(2)],
                marker=123,
            ),
            ChatMembersList(
                members=[create_chat_member(3), create_chat_member(4)],
                marker=None,
            ),
        ],
    )

    iterator = ChatMembersIterator(bot=bot, chat_id=1)
    members = [member async for member in iterator]

    assert len(members) == 4
    assert members[0].user_id == 1
    assert members[1].user_id == 2
    assert members[2].user_id == 3
    assert members[3].user_id == 4
    assert bot.get_members.await_count == 2


async def test_chat_members_iterator_no_members(bot: Bot) -> None:
    bot.get_members = AsyncMock(return_value=ChatMembersList(members=[], marker=None))

    iterator = ChatMembersIterator(bot=bot, chat_id=1)
    members = [member async for member in iterator]

    assert len(members) == 0
    bot.get_members.assert_awaited_once()


async def test_chat_members_iterator_with_user_ids(bot: Bot) -> None:
    bot.get_members = AsyncMock(
        side_effect=[
            ChatMembersList(members=[create_chat_member(1)], marker=None),
        ],
    )

    user_ids = [1, 2]
    iterator = ChatMembersIterator(bot=bot, chat_id=1, user_ids=user_ids)
    members = [member async for member in iterator]

    assert len(members) == 1
    assert bot.get_members.await_count == 1
    bot.get_members.assert_any_await(chat_id=1, user_ids=user_ids, marker=ANY, count=20)


async def test_chat_members_iterator_stops_on_none_marker(bot: Bot) -> None:
    """`marker=None` - последняя страница, запрашивать следующую нельзя.

    Для апи `marker: null` означает первую страницу, поэтому такой запрос
    вернул бы участников по кругу.
    """
    bot.get_members = AsyncMock(
        side_effect=[
            ChatMembersList(members=[create_chat_member(1)], marker=None),
            ChatMembersList(members=[create_chat_member(1)], marker=None),
        ],
    )

    iterator = ChatMembersIterator(bot=bot, chat_id=1)
    members = [member async for member in iterator]

    assert len(members) == 1
    assert bot.get_members.await_count == 1


async def test_chat_members_iterator_stops_on_omitted_marker(bot: Bot) -> None:
    bot.get_members = AsyncMock(
        return_value=ChatMembersList(members=[create_chat_member(1)]),
    )

    iterator = ChatMembersIterator(bot=bot, chat_id=1)
    members = [member async for member in iterator]

    assert [member.user_id for member in members] == [1]
    assert bot.get_members.await_count == 1
