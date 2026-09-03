try:
    from fastapi import APIRouter, FastAPI, Request, Response
    from fastapi.responses import JSONResponse
except ImportError as e:
    e.add_note("* Please run `pip install maxo[fastapi]`")
    raise

from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from typing import Any

from multidict import CIMultiDict, CIMultiDictProxy, MultiDict, MultiDictProxy

from maxo.transport.webhook.web.base import (
    Headers,
    LifecycleCallback,
    PathParams,
    QueryParams,
    WebAdapter,
    WebHandler,
    WebRequest,
)


class FastAPIWebRequest(WebRequest[Request]):
    __slots__ = ("_headers", "_query_params", "_request")

    def __init__(self, request: Request) -> None:
        self._request = request
        self._headers: Headers | None = None
        self._query_params: QueryParams | None = None

    @property
    def raw(self) -> Request:
        return self._request

    @property
    def client_ip(self) -> str | None:
        return self._request.client.host if self._request.client is not None else None

    async def json(self) -> dict[str, Any]:
        data: dict[str, Any] = await self._request.json()
        return data

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            self._headers = CIMultiDictProxy(CIMultiDict(self._request.headers.items()))
        return self._headers

    @property
    def query_params(self) -> QueryParams:
        if self._query_params is None:
            self._query_params = MultiDictProxy[str](
                MultiDict(self._request.query_params.multi_items()),
            )
        return self._query_params

    @property
    def path_params(self) -> PathParams:
        return self._request.path_params


class FastAPIAdapter(WebAdapter[FastAPI, Request, Response]):
    def bind_request(self, request: Request) -> WebRequest[Request]:
        return FastAPIWebRequest(request)

    def register(
        self,
        app: FastAPI,
        path: str,
        handler: WebHandler[Request, Response],
        *,
        on_startup: LifecycleCallback,
        on_shutdown: LifecycleCallback,
    ) -> None:
        async def endpoint(request: Request) -> Response:
            return await handler(self.bind_request(request))

        @asynccontextmanager
        async def lifespan(_router: APIRouter) -> AsyncGenerator[None, Any]:
            try:
                await on_startup(app)
                yield
            finally:
                await on_shutdown(app)

        router = APIRouter(lifespan=lifespan)
        router.add_api_route(path=path, endpoint=endpoint, methods=["POST"])
        app.include_router(router)

    def json_response(
        self,
        status_code: int,
        data: dict[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return JSONResponse(status_code=status_code, content=data, headers=headers)
