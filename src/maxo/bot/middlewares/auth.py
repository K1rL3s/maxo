from dataclasses import replace
from urllib.parse import urlsplit

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware


class AuthMiddleware(AsyncMiddleware):
    __slots__ = ("_token",)

    def __init__(self, token: str) -> None:
        self._token = token

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse:
        if not urlsplit(request.url).netloc:
            header = {"Authorization": self._token, **request.header}
            request = replace(request, header=header)
        return await next_handler(request)
