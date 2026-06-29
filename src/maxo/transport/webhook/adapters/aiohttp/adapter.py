from asyncio import Transport
from collections.abc import Awaitable, Callable, Mapping
from ipaddress import IPv4Address, IPv6Address
from json import JSONDecodeError
from typing import Any, cast

from aiohttp import ContentTypeError
from aiohttp.web import Application, Request
from aiohttp.web_response import Response, json_response

from maxo.transport.webhook.adapters.aiohttp.mapping import (
    AiohttpHeadersMapping,
    AiohttpQueryMapping,
)
from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.adapters.base_mapping import MappingABC


class AiohttpBoundRequest(BoundRequest[Request]):
    def __init__(self, request: Request) -> None:
        super().__init__(request)
        self._headers = AiohttpHeadersMapping(self.request.headers)
        self._query_params = AiohttpQueryMapping(self.request.query)

    async def json(self) -> dict[str, Any]:
        try:
            return cast(dict[str, Any], await self.request.json())
        except ContentTypeError as e:
            raise JSONDecodeError(str(e), "", 0) from e

    @property
    def client_ip(self) -> IPv4Address | IPv6Address | str | None:
        peer_name = cast(Transport, self.request.transport).get_extra_info("peername")
        if peer_name:
            return cast(IPv4Address | IPv6Address | str, peer_name[0])
        return None

    @property
    def headers(self) -> MappingABC[Mapping[str, Any]]:
        return self._headers

    @property
    def query_params(self) -> MappingABC[Mapping[str, Any]]:
        return self._query_params

    @property
    def path_params(self) -> dict[str, Any]:
        return self.request.match_info


class AiohttpWebAdapter(WebAdapter):
    def bind(self, request: Request) -> AiohttpBoundRequest:
        return AiohttpBoundRequest(request=request)

    def register(
        self,
        app: Application,
        path: str,
        handler: Callable[[BoundRequest[Any]], Awaitable[Any]],
        on_startup: Callable[..., Awaitable[Any]] | None = None,
        on_shutdown: Callable[..., Awaitable[Any]] | None = None,
    ) -> None:
        async def endpoint(request: Request) -> Any:
            return await handler(self.bind(request))

        app.router.add_route(method="POST", path=path, handler=endpoint)

        if on_startup is not None:
            app.on_startup.append(on_startup)
        if on_shutdown is not None:
            app.on_shutdown.append(on_shutdown)

    def create_json_response(self, status: int, payload: dict[str, Any]) -> Response:
        return json_response(status=status, data=payload)
