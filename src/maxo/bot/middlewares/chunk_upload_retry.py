from typing import Any

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware

from maxo.backoff import Backoff, BackoffConfig
from maxo.errors.network import MaxBotNetworkError

_SERVER_ERROR_STATUS = 500


class ChunkUploadRetryMiddleware(AsyncMiddleware):
    """
    Ретраит отправку чанка resumable upload: сетевые сбои и 5xx.

    Передаётся в `Bot.call_method(middleware=...)` и работает снаружи
    `NetworkErrorMiddleware`, поэтому видит уже переведённый
    `MaxBotNetworkError`/`MaxBotTimeoutError`, а не сырые исключения unihttp.
    """

    __slots__ = ("_backoff_config", "_max_retries")

    def __init__(self, max_retries: int, backoff_config: BackoffConfig) -> None:
        self._max_retries = max_retries
        self._backoff_config = backoff_config

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        backoff = Backoff(self._backoff_config)
        while True:
            try:
                response = await next_handler(request)
            except MaxBotNetworkError:
                if backoff.counter >= self._max_retries:
                    raise
            else:
                # 4xx считаем неретраибельными, ретраим только 5xx.
                if (
                    response.status_code < _SERVER_ERROR_STATUS
                    or backoff.counter >= self._max_retries
                ):
                    return response

            backoff.next()
            await backoff.sleep()
