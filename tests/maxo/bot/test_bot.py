import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.state import ClosedBotState, EmptyBotState, RunningBotState
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.errors import MaxBotApiError
from maxo.types import (
    BotInfo,
    GetSubscriptionsResult,
    SimpleQueryResult,
    Subscription,
)
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile
from tests.constants import NOW, TOKEN
from tests.factories import make_bot


class MockMaxBotApiError(MaxBotApiError):
    def __init__(self, message: str, code: str = "", error: str = "") -> None:
        self.message = message
        self.code = code
        self.error = error


@pytest.fixture
def bot() -> Bot:
    return make_bot()


async def test_bot_init(bot: Bot) -> None:
    assert bot.token == TOKEN
    assert isinstance(bot.state, EmptyBotState)


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


async def test_bot_start_and_close() -> None:
    bot = make_bot()
    assert isinstance(bot.state, EmptyBotState)

    with patch("maxo.bot.bot.MaxApiClient") as mock_api_client_class:
        mock_api_client = AsyncMock()
        mock_api_client_class.return_value = mock_api_client
        mock_api_client.call_method.return_value = BotInfo(
            user_id=1,
            is_bot=True,
            first_name="Test",
            username="testbot",
            last_activity_time=NOW,
        )

        await bot.start()
        assert isinstance(bot.state, RunningBotState)
        mock_api_client.call_method.assert_awaited_once()

        await bot.close()
        assert isinstance(bot.state, ClosedBotState)
        mock_api_client.close.assert_awaited_once()


async def test_bot_context(bot: Bot) -> None:
    with (
        patch("maxo.bot.bot.Bot.start", new_callable=AsyncMock) as mock_start,
        patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close,
    ):
        async with bot.context():
            mock_start.assert_awaited_once()
        mock_close.assert_awaited_once()


async def test_bot_call_method(bot: Bot) -> None:
    with patch.object(bot, "_state", MagicMock()) as mock_state:
        mock_state.api_client.call_method = AsyncMock(return_value="test_result")
        result: object = await bot.call_method(MagicMock())
        assert result == "test_result"
        mock_state.api_client.call_method.assert_awaited_once()


async def test_bot_silent_call_method(
    bot: Bot,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with patch.object(bot, "_state", MagicMock()) as mock_state:
        mock_state.api_client.call_method = AsyncMock(
            side_effect=MockMaxBotApiError("test error"),
        )
        await bot.silent_call_method(MagicMock())
        assert "Failed to make answer" in caplog.text


async def test_bot_download(bot: Bot) -> None:
    downloaded = io.BytesIO(b"downloaded")
    with patch.object(
        bot,
        "_state",
        MagicMock(),
    ) as mock_state:
        mock_state.api_client.download = AsyncMock(return_value=downloaded)
        result = await bot.download("https://example.com/file")
        assert result is downloaded
        mock_state.api_client.download.assert_awaited_once()


async def test_bot_defaults_and_retort(bot: Bot) -> None:
    assert bot.retort is not None
    assert bot.defaults is not None


async def test_close_on_empty_state_is_noop(bot: Bot) -> None:
    await bot.close()

    assert isinstance(bot.state, EmptyBotState)


async def test_close_twice_is_noop() -> None:
    bot = make_bot()
    api_client = AsyncMock()
    bot._state = RunningBotState(info=MagicMock(), api_client=api_client)

    await bot.close()
    await bot.close()

    api_client.close.assert_awaited_once()


async def test_bot_async_context_manager() -> None:
    bot = make_bot()

    with (
        patch("maxo.bot.bot.Bot.start", new_callable=AsyncMock) as mock_start,
        patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close,
    ):
        async with bot as entered:
            assert entered is bot

    mock_start.assert_awaited_once()
    mock_close.assert_awaited_once()


async def test_context_without_auto_close(bot: Bot) -> None:
    with (
        patch("maxo.bot.bot.Bot.start", new_callable=AsyncMock),
        patch("maxo.bot.bot.Bot.close", new_callable=AsyncMock) as mock_close,
    ):
        async with bot.context(auto_close=False):
            pass

    mock_close.assert_not_awaited()


async def test_bot_upload_media_resumable(bot: Bot) -> None:
    file = BufferedInputFile.file(b"payload", "f.bin")
    upload_result = UploadMediaResult(token="upload-token")  # noqa: S106

    with patch.object(bot, "_state", MagicMock()) as mock_state:
        mock_state.api_client.upload_resumable = AsyncMock(return_value=upload_result)
        result = await bot.upload_media_resumable("https://example.com/upload", file)

    assert result is upload_result
    mock_state.api_client.upload_resumable.assert_awaited_once_with(
        "https://example.com/upload",
        file,
        None,
    )


@pytest.mark.parametrize(
    ("active_url", "removed_urls"),
    [
        (None, ["https://one.example/webhook", "https://two.example/webhook"]),
        ("https://one.example/webhook", ["https://two.example/webhook"]),
        (
            "https://missing.example/webhook",
            [
                "https://one.example/webhook",
                "https://two.example/webhook",
            ],
        ),
    ],
)
async def test_clear_subscriptions(
    bot: Bot,
    active_url: str | None,
    removed_urls: list[str],
) -> None:
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
            Subscription(time=NOW, url="https://two.example/webhook"),
        ],
    )
    unsubscribe_results = [
        SimpleQueryResult(success=True) for _ in removed_urls
    ]

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ) as get_subscriptions,
        patch.object(
            Bot,
            "unsubscribe",
            new=AsyncMock(side_effect=unsubscribe_results),
        ) as unsubscribe,
    ):
        result = await bot.clear_subscriptions(active_url=active_url)

    get_subscriptions.assert_awaited_once_with()
    assert [call.kwargs["url"] for call in unsubscribe.await_args_list] == removed_urls
    assert result == unsubscribe_results


async def test_clear_subscriptions_handles_an_empty_list(bot: Bot) -> None:
    subscriptions = GetSubscriptionsResult(subscriptions=[])

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ),
        patch.object(Bot, "unsubscribe", new=AsyncMock()) as unsubscribe,
    ):
        result = await bot.clear_subscriptions()

    unsubscribe.assert_not_awaited()
    assert result == []
