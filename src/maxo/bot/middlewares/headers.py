import platform
from typing import Any
from urllib.parse import urlsplit

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware

from maxo.__meta__ import __version__

USER_AGENT = f"Python/{platform.python_version()} maxo/{__version__}"
CLIENT_HEADERS = {
    "User-Agent": USER_AGENT,
    "X-Max-Client-Name": "maxo",
    "X-Max-Client-Version": __version__,
    "X-Max-Client-Runtime": f"python{platform.python_version()}",
}


class UserAgentMiddleware(AsyncMiddleware):
    __slots__ = ()

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        for name, value in CLIENT_HEADERS.items():
            request.header.setdefault(name, value)
        return await next_handler(request)


class AuthMiddleware(AsyncMiddleware):
    __slots__ = ("_token",)

    def __init__(self, token: str) -> None:
        self._token = token

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        # `netloc` also catches "//host/path", which urljoin resolves elsewhere
        if not urlsplit(request.url).netloc:
            request.header.setdefault("Authorization", self._token)
        return await next_handler(request)
