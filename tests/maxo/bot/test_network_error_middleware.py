from unittest.mock import AsyncMock, MagicMock

import pytest
from unihttp.exceptions import NetworkError, RequestTimeoutError

from maxo.bot.middlewares import NetworkErrorMiddleware
from maxo.errors import MaxBotNetworkError, MaxBotTimeoutError, MaxoError


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (RequestTimeoutError("slow"), MaxBotTimeoutError),
        (NetworkError("dns"), MaxBotNetworkError),
        (TimeoutError("timed out"), MaxBotTimeoutError),
    ],
)
async def test_wraps_transport_errors(
    raised: Exception,
    expected: type[MaxBotNetworkError],
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
