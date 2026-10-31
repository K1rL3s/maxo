from unittest.mock import AsyncMock, MagicMock

import pytest
from unihttp.exceptions import (
    NetworkError,
    NonRetryableError,
    RequestTimeoutError,
    UniHTTPError,
)

from maxo.bot.middlewares import NetworkErrorMiddleware
from maxo.errors import (
    MaxBotNetworkError,
    MaxBotRequestError,
    MaxBotTimeoutError,
    MaxoError,
)


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (RequestTimeoutError("slow"), MaxBotTimeoutError),
        (NetworkError("dns"), MaxBotNetworkError),
        (TimeoutError("timed out"), MaxBotTimeoutError),
        (NonRetryableError("too many redirects"), MaxBotRequestError),
        (UniHTTPError("other aiohttp error"), MaxBotRequestError),
    ],
)
async def test_wraps_transport_errors(
    raised: Exception,
    expected: type[MaxoError],
) -> None:
    middleware = NetworkErrorMiddleware()
    next_handler = AsyncMock(side_effect=raised)

    with pytest.raises(expected) as exc_info:
        await middleware.handle(MagicMock(), next_handler)

    # Наружу торчит только maxo-ошибка, исходная лежит в __cause__.
    assert isinstance(exc_info.value, MaxoError)
    assert exc_info.value.__cause__ is raised


async def test_passes_response_through() -> None:
    middleware = NetworkErrorMiddleware()
    response = MagicMock()
    next_handler = AsyncMock(return_value=response)

    assert await middleware.handle(MagicMock(), next_handler) is response


async def test_other_errors_pass_as_is() -> None:
    middleware = NetworkErrorMiddleware()
    error = ValueError("not a network error")

    with pytest.raises(ValueError, match="not a network error"):
        await middleware.handle(MagicMock(), AsyncMock(side_effect=error))
