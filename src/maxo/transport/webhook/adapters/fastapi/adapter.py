from collections.abc import Awaitable, Callable, Mapping
from ipaddress import IPv4Address, IPv6Address
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.adapters.base_mapping import MappingABC
from maxo.transport.webhook.adapters.fastapi.mapping import (
    FastApiHeadersMapping,
    FastApiQueryMapping,
)


class FastApiBoundRequest(BoundRequest[Request]):
    def __init__(self, request: Request) -> None:
        super().__init__(request)
        self._headers = FastApiHeadersMapping(self.request.headers)
        self._query_params = FastApiQueryMapping(self.request.query_params)

    async def json(self) -> dict[str, Any]:
        return cast(dict[str, Any], await self.request.json())

    @property
    def client_ip(self) -> IPv4Address | IPv6Address | str | None:
        if self.request.client:
            return self.request.client.host
        return None

    @property
    def headers(self) -> MappingABC[Mapping[str, Any]]:
        return self._headers

    @property
    def query_params(self) -> MappingABC[Mapping[str, Any]]:
        return self._query_params

    @property
    def path_params(self) -> dict[str, Any]:
        return self.request.path_params


class FastApiWebAdapter(WebAdapter):
    def bind(self, request: Request) -> FastApiBoundRequest:
        return FastApiBoundRequest(request=request)

    def register(
        self,
        app: FastAPI,
        path: str,
        handler: Callable[[BoundRequest[Any]], Awaitable[Any]],
        on_startup: Callable[..., Awaitable[Any]] | None = None,
        on_shutdown: Callable[..., Awaitable[Any]] | None = None,
    ) -> None:
        """
        Регистрация роута.

        В реализации FastApiWebAdapter в register игнорируются переданные
        on_startup и on_shutdown. Разработчик должен сам определить lifespan,
        в котором вызовет engine.on_startup и engine.on_shutdown для корректной работы.
        """

        async def endpoint(request: Request) -> Any:
            return await handler(self.bind(request))

        app.add_api_route(path=path, endpoint=endpoint, methods=["POST"])

    def create_json_response(
        self,
        status: int,
        payload: dict[str, Any],
    ) -> JSONResponse:
        return JSONResponse(status_code=status, content=payload)
