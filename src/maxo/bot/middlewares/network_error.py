from typing import Any

from unihttp.exceptions import NetworkError, RequestTimeoutError
from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware

from maxo.errors.network import MaxBotTimeoutError, to_network_error


class NetworkErrorMiddleware(AsyncMiddleware):
    """Переводит транспортные ошибки unihttp в ошибки `maxo`."""

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        try:
            return await next_handler(request)
        except RequestTimeoutError as error:
            raise MaxBotTimeoutError(str(error) or type(error).__name__) from error
        except (NetworkError, TimeoutError) as error:
            raise to_network_error(error) from error
