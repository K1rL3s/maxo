from collections.abc import Mapping
from typing import Any

from aiohttp.web import Application, Request
from aiohttp.web_response import Response, json_response

from maxo.transport.webhook.web.base import (
    Headers,
    LifecycleCallback,
    PathParams,
    QueryParams,
    WebAdapter,
    WebHandler,
    WebRequest,
)


class AiohttpWebRequest(WebRequest[Request]):
    """Thin request wrapper over aiohttp request objects."""

    __slots__ = ("_request",)

    def __init__(self, request: Request) -> None:
        self._request = request

    @property
    def raw(self) -> Request:
        return self._request

    @property
    def client_ip(self) -> str | None:
        transport = self._request.transport
        if transport is None:
            return None

        if peer_name := transport.get_extra_info("peername"):
            return str(peer_name[0])
        return None

    async def json(self) -> dict[str, Any]:
        data: dict[str, Any] = await self._request.json()
        return data

    @property
    def headers(self) -> Headers:
        return self._request.headers

    @property
    def query_params(self) -> QueryParams:
        return self._request.query

    @property
    def path_params(self) -> PathParams:
        return self._request.match_info


class AiohttpAdapter(WebAdapter[Application, Request, Response]):
    """aiohttp adapter."""

    def bind_request(self, request: Request) -> WebRequest[Request]:
        return AiohttpWebRequest(request)

    def register(
        self,
        app: Application,
        path: str,
        handler: WebHandler[Request, Response],
        *,
        on_startup: LifecycleCallback,
        on_shutdown: LifecycleCallback,
    ) -> None:
        async def endpoint(request: Request) -> Response:
            return await handler(self.bind_request(request))

        app.router.add_route(method="POST", path=path, handler=endpoint)
        app.on_startup.append(on_startup)
        app.on_shutdown.append(on_shutdown)

    def json_response(
        self,
        status_code: int,
        data: dict[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return json_response(status=status_code, data=data, headers=headers)
