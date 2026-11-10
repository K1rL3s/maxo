from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from unihttp.exceptions import NetworkError, RequestTimeoutError, UniHTTPError
from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware

from maxo.errors.network import (
    MaxBotNetworkError,
    MaxBotRequestError,
    MaxBotTimeoutError,
)


@contextmanager
def translate_network_errors() -> Iterator[None]:
    try:
        yield
    except (RequestTimeoutError, TimeoutError) as error:
        raise MaxBotTimeoutError(_text(error)) from error
    except NetworkError as error:
        raise MaxBotNetworkError(_text(error)) from error
    except UniHTTPError as error:
        # NonRetryableError and the rest: not a network failure, don't retry
        raise MaxBotRequestError(_text(error)) from error


def _text(error: Exception) -> str:
    return str(error) or type(error).__name__


class NetworkErrorMiddleware(AsyncMiddleware):
    """Переводит транспортные ошибки unihttp в ошибки `maxo`."""

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        with translate_network_errors():
            return await next_handler(request)
