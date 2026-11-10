from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.backoff import BackoffConfig
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    is_attachment_not_ready,
)
from maxo.bot.middlewares.attachment_retry import NOT_READY_CODE
from maxo.errors.api import (
    MaxBotBadRequestError,
    MaxBotForbiddenError,
    MaxBotTooManyRequestsError,
    raise_api_error,
)

FAST_BACKOFF = BackoffConfig(min_delay=0.0, max_delay=0.01, factor=2.0, jitter=0.0)


def not_ready_error() -> MaxBotBadRequestError:
    return MaxBotBadRequestError(
        NOT_READY_CODE,
        "",
        "Key: errors.process.attachment.file.not.processed",
    )


def other_bad_request() -> MaxBotBadRequestError:
    return MaxBotBadRequestError(
        "proto.payload",
        "",
        "Must be only one file attachment in message",
    )


def test_is_attachment_not_ready_by_code() -> None:
    assert is_attachment_not_ready(not_ready_error()) is True


def test_is_attachment_not_ready_by_message() -> None:
    error = MaxBotBadRequestError("", "", "something not.processed yet")
    assert is_attachment_not_ready(error) is True


def test_is_attachment_not_ready_from_real_api_payload() -> None:
    payload = {
        "error_code": "proto.payload",
        "error_data": NOT_READY_CODE,
        "message": "cannot process attachment",
    }
    with pytest.raises(MaxBotBadRequestError) as exc_info:
        raise_api_error(400, payload)

    assert is_attachment_not_ready(exc_info.value) is True


def test_is_attachment_not_ready_false_for_other() -> None:
    assert is_attachment_not_ready(other_bad_request()) is False


async def test_returns_result_without_retry_on_success() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=10,
        backoff_config=FAST_BACKOFF,
    )
    sentinel = MagicMock()
    next_handler = AsyncMock(return_value=sentinel)

    with patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
        result = await middleware.handle(MagicMock(), next_handler)

    assert result is sentinel
    next_handler.assert_awaited_once()
    sleep_mock.assert_not_awaited()


async def test_retries_until_ready() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=10,
        backoff_config=FAST_BACKOFF,
    )
    sentinel = MagicMock()
    next_handler = AsyncMock(
        side_effect=[not_ready_error(), not_ready_error(), sentinel],
    )

    with patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
        result = await middleware.handle(MagicMock(), next_handler)

    assert result is sentinel
    assert next_handler.await_count == 3
    assert sleep_mock.await_count == 2


async def test_reraises_non_not_ready_bad_request_without_retry() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=10,
        backoff_config=FAST_BACKOFF,
    )
    next_handler = AsyncMock(side_effect=other_bad_request())

    with (
        patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock,
        pytest.raises(MaxBotBadRequestError, match=r"proto\.payload"),
    ):
        await middleware.handle(MagicMock(), next_handler)

    next_handler.assert_awaited_once()
    sleep_mock.assert_not_awaited()


async def test_reraises_other_api_errors_without_retry() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=10,
        backoff_config=FAST_BACKOFF,
    )
    next_handler = AsyncMock(side_effect=MaxBotForbiddenError("", "", ""))

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(MaxBotForbiddenError),
    ):
        await middleware.handle(MagicMock(), next_handler)

    next_handler.assert_awaited_once()


async def test_does_not_retry_too_many_requests() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=10,
        backoff_config=FAST_BACKOFF,
    )
    next_handler = AsyncMock(side_effect=MaxBotTooManyRequestsError("", "", ""))

    with pytest.raises(MaxBotTooManyRequestsError):
        await middleware.handle(MagicMock(), next_handler)

    next_handler.assert_awaited_once()


async def test_raises_after_exhausting_retries() -> None:
    middleware = AttachmentNotReadyRetryMiddleware(
        max_retries=3,
        backoff_config=FAST_BACKOFF,
    )
    next_handler = AsyncMock(side_effect=not_ready_error())

    with (
        patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock,
        pytest.raises(MaxBotBadRequestError, match=NOT_READY_CODE),
    ):
        await middleware.handle(MagicMock(), next_handler)

    assert next_handler.await_count == 4
    assert sleep_mock.await_count == 3
