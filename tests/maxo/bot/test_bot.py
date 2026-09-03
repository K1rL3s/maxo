import io
from asyncio import CancelledError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.state import ClosedBotState, EmptyBotState, RunningBotState
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.errors import MaxBotApiError, UnsubscribeError
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
    ("active_urls", "removed_urls"),
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
        (["https://one.example/webhook"], ["https://two.example/webhook"]),
        (
            [
                "https://one.example/webhook",
                "https://two.example/webhook",
            ],
            [],
        ),
    ],
)
async def test_clear_subscriptions(
    bot: Bot,
    active_urls: str | list[str] | None,
    removed_urls: list[str],
) -> None:
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
            Subscription(time=NOW, url="https://two.example/webhook"),
        ],
    )

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ) as get_subscriptions,
        patch.object(Bot, "unsubscribe", new=AsyncMock()) as unsubscribe,
    ):
        result = await bot.clear_subscriptions(active_urls=active_urls)

    get_subscriptions.assert_awaited_once_with()
    assert [call.kwargs["url"] for call in unsubscribe.await_args_list] == removed_urls
    assert [subscription.url for subscription in result.removed] == removed_urls
    assert [subscription.url for subscription in result.kept] == [
        subscription.url
        for subscription in subscriptions.subscriptions
        if subscription.url not in removed_urls
    ]


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
    assert result.removed == []
    assert result.kept == []


async def test_clear_subscriptions_reports_failed_urls(bot: Bot) -> None:
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
            Subscription(time=NOW, url="https://two.example/webhook"),
        ],
    )
    failure = MockMaxBotApiError("boom")

    async def unsubscribe_side_effect(url: str) -> SimpleQueryResult:
        if url == "https://one.example/webhook":
            raise failure
        return SimpleQueryResult(success=True)

    unsubscribe = AsyncMock(side_effect=unsubscribe_side_effect)

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ),
        patch.object(Bot, "unsubscribe", new=unsubscribe),
        pytest.raises(ExceptionGroup) as exc_info,
    ):
        await bot.clear_subscriptions()

    errors = exc_info.value.exceptions
    assert len(errors) == 1
    error = errors[0]
    assert isinstance(error, UnsubscribeError)
    assert error.url == "https://one.example/webhook"
    assert error.error is failure
    assert error.__cause__ is failure
    # Упавший запрос не отменяет остальные
    assert [call.kwargs["url"] for call in unsubscribe.await_args_list] == [
        "https://one.example/webhook",
        "https://two.example/webhook",
    ]


async def test_clear_subscriptions_collects_every_error(bot: Bot) -> None:
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
            Subscription(time=NOW, url="https://two.example/webhook"),
        ],
    )

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ),
        patch.object(
            Bot,
            "unsubscribe",
            new=AsyncMock(side_effect=MockMaxBotApiError("boom")),
        ),
        pytest.raises(ExceptionGroup) as exc_info,
    ):
        await bot.clear_subscriptions()

    assert [
        error.url
        for error in exc_info.value.exceptions
        if isinstance(error, UnsubscribeError)
    ] == [
        "https://one.example/webhook",
        "https://two.example/webhook",
    ]


async def test_clear_subscriptions_does_not_wrap_cancellation(bot: Bot) -> None:
    # CancelledError нельзя прятать в UnsubscribeError - она едет в группе как есть.
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
        ],
    )

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ),
        patch.object(Bot, "unsubscribe", new=AsyncMock(side_effect=CancelledError)),
        pytest.raises(BaseExceptionGroup) as exc_info,
    ):
        await bot.clear_subscriptions()

    # Группа с BaseException не сужается до ExceptionGroup.
    assert not isinstance(exc_info.value, ExceptionGroup)
    assert [type(error) for error in exc_info.value.exceptions] == [CancelledError]


async def test_clear_subscriptions_keeps_errors_next_to_cancellation(bot: Bot) -> None:
    # Отмена одного запроса не должна прятать провалы остальных.
    subscriptions = GetSubscriptionsResult(
        subscriptions=[
            Subscription(time=NOW, url="https://one.example/webhook"),
            Subscription(time=NOW, url="https://two.example/webhook"),
        ],
    )
    failure = MockMaxBotApiError("boom")

    async def unsubscribe_side_effect(url: str) -> SimpleQueryResult:
        if url == "https://one.example/webhook":
            raise CancelledError
        raise failure

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(return_value=subscriptions),
        ),
        patch.object(
            Bot,
            "unsubscribe",
            new=AsyncMock(side_effect=unsubscribe_side_effect),
        ),
        pytest.raises(BaseExceptionGroup) as exc_info,
    ):
        await bot.clear_subscriptions()

    cancelled, unsubscribe_error = exc_info.value.exceptions
    assert isinstance(cancelled, CancelledError)
    assert isinstance(unsubscribe_error, UnsubscribeError)
    assert unsubscribe_error.url == "https://two.example/webhook"
    assert unsubscribe_error.error is failure


async def test_clear_subscriptions_propagates_get_subscriptions_error(bot: Bot) -> None:
    unsubscribe = AsyncMock()

    with (
        patch.object(
            Bot,
            "get_subscriptions",
            new=AsyncMock(side_effect=MockMaxBotApiError("boom")),
        ),
        patch.object(Bot, "unsubscribe", new=unsubscribe),
        pytest.raises(MaxBotApiError),
    ):
        await bot.clear_subscriptions()

    unsubscribe.assert_not_awaited()
