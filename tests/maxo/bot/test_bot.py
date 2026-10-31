import asyncio
from asyncio import CancelledError
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession
from unihttp.http import UploadFile

from maxo.bot.bot import Bot
from maxo.bot.client import default_media_client
from maxo.bot.media import Media
from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.bot.middlewares import AuthMiddleware
from maxo.bot.upload import ProcessingConfig, UploadConfig, UploadMethod
from maxo.errors import MaxBotApiError, UnsubscribeError
from maxo.types import (
    BotInfo,
    GetSubscriptionsResult,
    SimpleQueryResult,
    Subscription,
)
from tests.constants import BOT_ID, NOW, TOKEN
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


def test_default_upload_config_is_not_shared() -> None:
    first = make_bot()
    second = make_bot()

    first.media.config.method = UploadMethod.SINGLE

    assert second.media.config.method is UploadMethod.AUTO
    assert first.media.config is not second.media.config


def test_explicit_media_and_processing_are_preserved() -> None:
    media = Media(config=UploadConfig(method=UploadMethod.RESUMABLE))
    processing = ProcessingConfig(not_ready_max_retries=1)
    bot = make_bot(media=media, processing=processing)

    assert bot.media is media
    assert bot._processing is processing


async def test_bot_close(mock_bot: Bot, mock_client: AsyncMock) -> None:
    await mock_bot.close()

    # Клиент передали снаружи - закрывать его боту нельзя.
    mock_client.close.assert_not_awaited()
    assert mock_bot.client is mock_client


async def test_closed_own_client_is_recreated(mock_bot: Bot) -> None:
    """Как в aiogram: после `close()` бот снова рабочий."""
    mock_bot._owns_client = True
    first = mock_bot.client

    await mock_bot.close()

    first.close.assert_awaited_once()  # type: ignore[attr-defined]
    with patch("maxo.bot.bot.default_client", return_value=AsyncMock()) as factory:
        assert mock_bot.client is factory.return_value


async def test_async_with_resolves_info_and_closes(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    mock_bot._owns_client = True
    mock_client.call_method.return_value = bot_info

    async with mock_bot as bot:
        assert bot is mock_bot
        assert (await bot.me()).user_id == BOT_ID

    mock_client.call_method.assert_awaited_once()
    mock_client.close.assert_awaited_once()


async def test_bot_call_method(mock_bot: Bot, mock_client: AsyncMock) -> None:
    """`call_method` doesn't resolve bot info as a side effect."""
    mock_client.call_method.return_value = "test_result"

    result: object = await mock_bot.call_method(MagicMock())

    assert result == "test_result"
    mock_client.call_method.assert_awaited_once()


async def test_close_before_first_request_is_noop(bot: Bot) -> None:
    await bot.close()

    assert bot._client is None  # nothing was created, nothing to close


async def test_close_twice_is_noop(mock_bot: Bot, mock_client: AsyncMock) -> None:
    mock_bot._owns_client = True

    await mock_bot.close()
    await mock_bot.close()

    mock_client.close.assert_awaited_once()


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

    mock_client.call_method.side_effect = None
    mock_client.call_method.return_value = bot_info

    assert (await mock_bot.me()).user_id == BOT_ID
    assert mock_client.call_method.await_count == 2


async def test_me_fetches_info_once_and_caches_it(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    """Без `async with bot` (вебхук, тесты) `me()` сам запрашивает информацию о боте."""
    mock_client.call_method.return_value = bot_info

    first = await mock_bot.me()
    second = await mock_bot.me()

    assert first is second
    assert first.user_id == BOT_ID
    mock_client.call_method.assert_awaited_once()


async def test_concurrent_me_calls_api_once(
    mock_bot: Bot,
    mock_client: AsyncMock,
    bot_info: BotInfo,
) -> None:
    async def slow_info(*_: object, **__: object) -> BotInfo:
        await asyncio.sleep(0)  # let the other tasks reach the lock
        return bot_info

    mock_client.call_method.side_effect = slow_info

    results = await asyncio.gather(*(mock_bot.me() for _ in range(5)))

    assert all(result is bot_info for result in results)
    mock_client.call_method.assert_awaited_once()


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


@pytest.mark.parametrize(
    ("method_name", "kwargs"),
    [
        ("add_members", {"chat_id": 1, "user_ids": [2]}),
        ("delete_chat", {"chat_id": 1}),
        ("edit_bot_info", {"first_name": "Bot"}),
        ("get_chat_by_link", {"chat_link": "channel"}),
        ("get_chats", {}),
    ],
)
async def test_deprecated_method_warns_at_caller(
    bot: Bot,
    method_name: str,
    kwargs: dict[str, object],
) -> None:
    with (
        patch.object(Bot, "call_method", AsyncMock()),
        pytest.warns(DeprecationWarning, match="MAX") as record,
    ):
        await getattr(bot, method_name)(**kwargs)

    assert record[0].filename == __file__


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


async def test_media_uses_given_client_without_token() -> None:
    """File-host uploads go through the `Media` client, not the API one, and
    without a token: the `Media` chain has no `AuthMiddleware`."""
    api, media_client = AsyncMock(), AsyncMock()
    bot = make_bot(client=api, media=Media(media_client))

    await bot.media.call_method(
        UploadMedia(
            upload_url="https://fu.example/upload",
            file=UploadFile(file=b"data", filename="f.bin"),
        ),
    )

    assert bot.media.client is media_client
    api.call_method.assert_not_awaited()
    used = media_client.call_method.await_args.kwargs["middleware"]
    assert used == bot.media.middleware
    assert not any(isinstance(m, AuthMiddleware) for m in used)


async def test_bot_calls_only_the_api_client() -> None:
    """`Bot` has no client choice: everything called through it goes to the API."""
    api, media_client = AsyncMock(), AsyncMock()
    api.call_method.return_value = make_bot_info()
    bot = make_bot(client=api, media=Media(media_client))

    await bot.get_my_info()

    media_client.call_method.assert_not_awaited()
    used = api.call_method.await_args.kwargs["middleware"]
    assert any(isinstance(m, AuthMiddleware) for m in used)


async def test_close_closes_only_own_clients() -> None:
    external = AsyncMock()
    bot = make_bot(media=Media(external))
    own_api = bot.client

    with patch.object(own_api, "close", new_callable=AsyncMock) as close_api:
        await bot.close()

    close_api.assert_awaited_once()
    external.close.assert_not_awaited()


async def test_own_media_client_is_closed_with_bot() -> None:
    bot = make_bot()
    media_client = bot.media.client

    with patch.object(media_client, "close", new_callable=AsyncMock) as close_media:
        await bot.close()

    close_media.assert_awaited_once()


async def test_default_media_client_has_no_total_timeout() -> None:
    client = default_media_client()
    try:
        timeout = client._session.timeout
        assert timeout.total is None
        assert timeout.sock_read is not None
    finally:
        await client.close()


async def test_default_media_client_takes_own_session() -> None:
    """The session is replaceable, e.g. with an aiohttp session behind a proxy."""
    session = ClientSession()
    client = default_media_client(session=session)
    try:
        assert client._session is session
    finally:
        await client.close()
