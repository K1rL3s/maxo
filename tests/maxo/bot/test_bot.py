from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.errors import MaxBotApiError
from maxo.errors.state import StateError
from maxo.types import BotInfo
from tests.constants import BOT_ID, TOKEN
from tests.factories import make_bot, make_bot_info


class MockMaxBotApiError(MaxBotApiError):
    def __init__(self, message: str, code: str = "", error: str = "") -> None:
        self.message = message
        self.code = code
        self.error = error


@pytest.fixture
def mock_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot(mock_client: AsyncMock) -> Bot:
    return make_bot(client=mock_client)


@pytest.fixture
def bot_info() -> BotInfo:
    return make_bot_info()


async def test_bot_init(bot: Bot) -> None:
    assert bot.token == TOKEN
    assert bot.started is False
    assert bot.closed is False
    with pytest.raises(StateError, match="Bot info is not resolved yet"):
        _ = bot.info


def test_default_upload_config_is_not_shared() -> None:
    first = make_bot()
    second = make_bot()

    first.upload_config.method = UploadMethod.SINGLE

    assert second.upload_config.method is UploadMethod.AUTO
    assert first.upload_config is not second.upload_config


def test_explicit_upload_config_is_preserved() -> None:
    config = UploadConfig(method=UploadMethod.RESUMABLE)
    bot = make_bot(upload_config=config)

    assert bot.upload_config is config


async def test_bot_close(mock_bot: Bot, mock_client: AsyncMock) -> None:
    await mock_bot.close()

    assert mock_bot.closed is True
    # Клиент передали снаружи - закрывать его боту нельзя.
    mock_client.close.assert_not_awaited()


async def test_bot_context(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context(get_my_info=False):
            pass
        mock_close.assert_awaited_once()


async def test_bot_context_fetches_info_by_default(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    mock_client.call_method.return_value = bot_info

    async with mock_bot.context():
        assert mock_bot.info.user_id == BOT_ID

    mock_client.call_method.assert_awaited_once()


async def test_bot_call_method(mock_bot: Bot, mock_client: AsyncMock) -> None:
    """`call_method` no longer resolves `.info` as a side effect."""
    mock_client.call_method.return_value = "test_result"

    result: object = await mock_bot.call_method(MagicMock())

    assert result == "test_result"
    mock_client.call_method.assert_awaited_once()
    with pytest.raises(StateError, match="Bot info is not resolved yet"):
        _ = mock_bot.info


async def test_close_on_empty_state_is_noop(bot: Bot) -> None:
    await bot.close()

    assert bot.closed is False


async def test_close_twice_is_noop(mock_bot: Bot, mock_client: AsyncMock) -> None:
    mock_bot._owns_client = True

    await mock_bot.close()
    await mock_bot.close()

    mock_client.close.assert_awaited_once()


async def test_context_without_auto_close(bot: Bot) -> None:
    with patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close:
        async with bot.context(auto_close=False, get_my_info=False):
            pass

    mock_close.assert_not_awaited()


async def test_client_access_never_hits_network(
    mock_bot: Bot,
    mock_client: AsyncMock,
) -> None:
    """Accessing `.client` repeatedly must not touch the network at all."""
    assert mock_bot.client is mock_client
    assert mock_bot.client is mock_client

    mock_client.call_method.assert_not_awaited()


async def test_get_my_info_retries_after_previous_failure(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    mock_client.call_method.side_effect = MockMaxBotApiError("boom")

    with pytest.raises(MaxBotApiError):
        await mock_bot.get_my_info()

    assert mock_bot.started is False
    with pytest.raises(StateError, match="Bot info is not resolved yet"):
        _ = mock_bot.info

    mock_client.call_method.side_effect = None
    mock_client.call_method.return_value = bot_info

    await mock_bot.get_my_info()
    assert mock_bot.info.user_id == BOT_ID


async def test_get_my_info_starts_lazily_and_caches_info(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    mock_client.call_method.return_value = bot_info

    info = await mock_bot.get_my_info()

    assert info is not None
    assert info.user_id == BOT_ID
    assert mock_bot.info is info
    assert mock_bot.started is True


async def test_get_my_info_always_hits_network(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    """Unlike `start()`, repeated `get_my_info()` calls must not be cached —
    it's the "give me fresh data now" escape hatch."""
    mock_client.call_method.return_value = bot_info

    await mock_bot.get_my_info()
    await mock_bot.get_my_info()

    assert mock_client.call_method.await_count == 2
