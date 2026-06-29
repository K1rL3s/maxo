from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.state import ClosedBotState, EmptyBotState, RunningBotState
from maxo.errors import MaxBotApiError
from maxo.types import BotInfo

TOKEN = "f9LHod"  # noqa: S105


class MockMaxBotApiError(MaxBotApiError):
    def __init__(self, message: str, code: str = "", error: str = ""):
        self.message = message
        self.code = code
        self.error = error


@pytest.fixture
def bot():
    return Bot(token=TOKEN)


async def test_bot_init(bot: Bot):
    assert bot.token == TOKEN
    assert isinstance(bot.state, EmptyBotState)


async def test_bot_start_and_close():
    bot = Bot(token=TOKEN)
    assert isinstance(bot.state, EmptyBotState)

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=datetime.now(UTC),
        )

        await bot.start()
        assert isinstance(bot.state, RunningBotState)
        mock_api_client.call_method.assert_awaited_once()

        await bot.close()
        assert isinstance(bot.state, ClosedBotState)
        mock_api_client.close.assert_awaited_once()


async def test_bot_context(bot: Bot):
    with (
        patch("maxo.bot.bot.Bot.start", new_callable=AsyncMock) as mock_start,
        patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close,
    ):
        async with bot.context():
            mock_start.assert_awaited_once()
        mock_close.assert_awaited_once()


async def test_bot_call_method(bot: Bot):
    with patch.object(bot, "_state", MagicMock()) as mock_state:
        mock_state.api_client.call_method = AsyncMock(return_value="test_result")
        result = await bot.call_method(MagicMock())
        assert result == "test_result"
        mock_state.api_client.call_method.assert_awaited_once()


async def test_bot_silent_call_method(bot: Bot, caplog):
    with patch.object(bot, "_state", MagicMock()) as mock_state:
        mock_state.api_client.call_method = AsyncMock(
            side_effect=MockMaxBotApiError("test error"),
        )
        await bot.silent_call_method(MagicMock())
        assert "Failed to make answer" in caplog.text


async def test_bot_download(bot: Bot):
    with patch.object(
        bot,
        "_state",
        MagicMock(),
    ) as mock_state:  # Patch private attribute
        mock_state.api_client.download = AsyncMock(return_value="downloaded")
        result = await bot.download("https://example.com/file")
        assert result == "downloaded"
        mock_state.api_client.download.assert_awaited_once()
