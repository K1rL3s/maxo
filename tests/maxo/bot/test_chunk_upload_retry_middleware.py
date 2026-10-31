"""Retries of a resumable-upload chunk; ported from upstream `test_upload.py`."""

from collections.abc import Sequence
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from maxo.backoff import BackoffConfig
from maxo.bot.middlewares import ChunkUploadRetryMiddleware
from maxo.bot.upload import UploadConfig
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotNetworkError,
    MaxBotRequestError,
    MaxBotServerError,
    MaxBotTimeoutError,
)

_BACKOFF = UploadConfig().chunk_backoff


def _response(status_code: int) -> MagicMock:
    return MagicMock(status_code=status_code)


def _server_error() -> MaxBotServerError:
    return MaxBotServerError(code="", error="x", message="x")


async def _handle(
    outcomes: Sequence[object],
    retries: int,
    backoff: BackoffConfig = _BACKOFF,
) -> tuple[object, AsyncMock, AsyncMock]:
    middleware = ChunkUploadRetryMiddleware(max_retries=retries, backoff_config=backoff)
    next_handler = AsyncMock(side_effect=outcomes)
    with patch("asyncio.sleep", new_callable=AsyncMock) as sleep:
        result = await middleware.handle(MagicMock(), next_handler)
    return result, next_handler, sleep


async def test_server_error_is_retried_then_succeeds() -> None:
    ok = _response(200)

    result, next_handler, _ = await _handle([_server_error(), ok], retries=3)

    assert result is ok
    assert next_handler.await_count == 2


async def test_server_error_is_reraised_after_retries() -> None:
    with pytest.raises(MaxBotServerError):
        await _handle([_server_error(), _server_error()], retries=1)


@pytest.mark.parametrize(
    "error",
    [
        MaxBotBadRequestError(code="", error="x", message="x"),
        MaxBotApiError(code="", error="x", message="x"),
        MaxBotRequestError("bad url"),
    ],
)
async def test_error_is_not_retried(error: Exception) -> None:
    middleware = ChunkUploadRetryMiddleware(max_retries=3, backoff_config=_BACKOFF)
    next_handler = AsyncMock(side_effect=error)

    with pytest.raises(type(error)):
        await middleware.handle(MagicMock(), next_handler)

    assert next_handler.await_count == 1


async def test_timeout_is_retried_then_succeeds() -> None:
    ok = _response(200)

    result, next_handler, _ = await _handle(
        [MaxBotTimeoutError("timed out"), ok],
        retries=3,
    )

    assert result is ok
    assert next_handler.await_count == 2


async def test_network_error_is_reraised_after_retries() -> None:
    errors = [MaxBotNetworkError("boom") for _ in range(3)]

    with pytest.raises(MaxBotNetworkError, match="boom"):
        await _handle(errors, retries=2)


async def test_first_retry_waits_backoff_min_delay() -> None:
    _, _, sleep = await _handle([_server_error(), _response(200)], retries=3)

    # The first pause is exactly `min_delay`, not doubled
    assert sleep.await_args_list[0].args[0] == _BACKOFF.min_delay
