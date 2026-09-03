from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.enums import TextFormat
from maxo.omit import Omitted
from maxo.types.chat import Chat
from maxo.types.chat_members_list import ChatMembersList
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.message import Message
from maxo.types.message_list import MessageList
from maxo.types.send_message_result import SendMessageResult
from maxo.types.simple_query_result import SimpleQueryResult
from tests.constants import NOW


class MockChatFacade(ChatMethodsFacade):
    def __init__(self, bot: MagicMock, chat_id: int) -> None:
        self._bot = bot
        self._chat_id = chat_id

    @property
    def chat_id(self) -> int:
        return self._chat_id


@pytest.fixture
def mock_bot() -> MagicMock:
    bot = MagicMock()
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=MagicMock(spec=Message)),
    )
    bot.get_chat = AsyncMock(return_value=MagicMock(spec=Chat))
    bot.get_members = AsyncMock(return_value=MagicMock(spec=ChatMembersList))
    bot.leave_chat = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.get_messages = AsyncMock(return_value=MagicMock(spec=MessageList))
    return bot


@pytest.fixture
def facade(mock_bot: MagicMock) -> MockChatFacade:
    return MockChatFacade(mock_bot, chat_id=12345)


async def test_chat_id_property(facade: MockChatFacade) -> None:
    assert facade.chat_id == 12345


async def test_get_chat(facade: MockChatFacade, mock_bot: MagicMock) -> None:
    result = await facade.get_chat()

    mock_bot.get_chat.assert_called_once_with(chat_id=12345)
    assert isinstance(result, Chat)


async def test_leave_chat(facade: MockChatFacade, mock_bot: MagicMock) -> None:
    result = await facade.leave_chat()

    mock_bot.leave_chat.assert_called_once_with(chat_id=12345)
    assert result.success is True


async def test_get_members_no_params(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_members()

    mock_bot.get_members.assert_called_once_with(
        chat_id=12345,
        count=Omitted(),
        marker=Omitted(),
        user_ids=Omitted(),
    )


async def test_get_members_with_count(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_members(count=50)

    mock_bot.get_members.assert_called_once_with(
        chat_id=12345,
        count=50,
        marker=Omitted(),
        user_ids=Omitted(),
    )


async def test_get_members_with_all_params(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_members(count=100, marker=555, user_ids=[1, 2, 3])

    mock_bot.get_members.assert_called_once_with(
        chat_id=12345,
        count=100,
        marker=555,
        user_ids=[1, 2, 3],
    )


async def test_get_messages_no_params(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_messages()

    mock_bot.get_messages.assert_called_once_with(
        chat_id=12345,
        count=Omitted(),
        from_=Omitted(),
        message_ids=Omitted(),
        to=Omitted(),
    )


async def test_get_messages_with_count(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_messages(count=20)

    mock_bot.get_messages.assert_called_once_with(
        chat_id=12345,
        count=20,
        from_=Omitted(),
        message_ids=Omitted(),
        to=Omitted(),
    )


async def test_get_messages_with_datetime_params(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    from_time = NOW
    to_time = datetime(2026, 1, 31, tzinfo=UTC)

    await facade.get_messages(from_=from_time, to=to_time)

    mock_bot.get_messages.assert_called_once_with(
        chat_id=12345,
        count=Omitted(),
        from_=from_time,
        message_ids=Omitted(),
        to=to_time,
    )


async def test_get_messages_with_message_ids(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_messages(message_ids=["mid1", "mid2", "mid3"])

    mock_bot.get_messages.assert_called_once_with(
        chat_id=12345,
        count=Omitted(),
        from_=Omitted(),
        message_ids=["mid1", "mid2", "mid3"],
        to=Omitted(),
    )


async def test_send_message_minimal(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    with patch.object(
        facade,
        "build_attachments",
        new_callable=AsyncMock,
    ) as mock_build:
        mock_build.return_value = []

        result = await facade.send_message(text="Hello")

        mock_build.assert_called_once_with(base=[], keyboard=None, files=None)
        mock_bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Hello",
            attachments=[],
            link=None,
            notify=True,
            format=Omitted(),
            disable_link_preview=Omitted(),
        )
        assert isinstance(result, Message)


async def test_send_message_with_all_params(
    facade: MockChatFacade,
    mock_bot: MagicMock,
) -> None:
    with patch.object(
        facade,
        "build_attachments",
        new_callable=AsyncMock,
    ) as mock_build:
        mock_build.return_value = [MagicMock()]
        keyboard = [[MagicMock()]]
        media = [MagicMock()]
        attachments = [MagicMock()]
        link = MagicMock()

        await facade.send_message(
            text="Hello World",
            link=link,
            notify=False,
            format=TextFormat.MARKDOWN,
            disable_link_preview=True,
            keyboard=keyboard,
            media=media,
            attachments=attachments,
        )

        mock_build.assert_called_once_with(
            base=attachments,
            keyboard=keyboard,
            files=media,
        )
        mock_bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Hello World",
            attachments=mock_build.return_value,
            link=link,
            notify=False,
            format=TextFormat.MARKDOWN,
            disable_link_preview=True,
        )


async def test_send_message_without_attachments(facade: MockChatFacade) -> None:
    with patch.object(
        facade,
        "build_attachments",
        new_callable=AsyncMock,
    ) as mock_build:
        mock_build.return_value = []

        await facade.send_message(text="No attachments")

        mock_build.assert_called_once_with(base=[], keyboard=None, files=None)


async def test_send_message_with_keyboard_only(facade: MockChatFacade) -> None:
    with patch.object(
        facade,
        "build_attachments",
        new_callable=AsyncMock,
    ) as mock_build:
        mock_build.return_value = [MagicMock()]
        keyboard = [[MagicMock()]]

        await facade.send_message(text="With keyboard", keyboard=keyboard)

        mock_build.assert_called_once_with(base=[], keyboard=keyboard, files=None)
