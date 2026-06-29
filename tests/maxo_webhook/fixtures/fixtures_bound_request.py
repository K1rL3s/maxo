from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Never

from maxo.transport.webhook.adapters.base_adapter import BoundRequest, WebAdapter
from maxo.transport.webhook.adapters.base_mapping import MappingABC


class DummyAdapter(WebAdapter):
    def bind(self, request: Any) -> Never:
        raise NotImplementedError("DummyAdapter.bind is not implemented")

    def register(
        self,
        app: Any,
        path: str,
        handler: Callable[[BoundRequest[Any]], Awaitable[Any]],
        on_startup: Callable[..., Awaitable[Any]] | None = None,
        on_shutdown: Callable[..., Awaitable[Any]] | None = None,
    ) -> Never:
        raise NotImplementedError("DummyAdapter.register is not implemented")

    def create_json_response(self, status: int, payload: dict[str, Any]) -> Any:
        return status, payload


class DummyRequest:
    def __init__(
        self,
        *,
        path_params: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        ip: str | None = None,
    ) -> None:
        self.path_params = path_params or {}
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.ip = ip


class DummyMapping(MappingABC[Mapping[str, Any]]):
    def getlist(self, name: str) -> list[Any]:
        value = self.get(name)
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


class DummyBoundRequest(BoundRequest[DummyRequest]):
    def __init__(self, request: DummyRequest | None = None) -> None:
        super().__init__(request or DummyRequest())

    async def json(self) -> dict[str, Any]:
        return {}

    @property
    def client_ip(self) -> str | None:
        return self.request.ip

    @property
    def headers(self) -> MappingABC[Mapping[str, Any]]:
        return DummyMapping(self.request.headers)

    @property
    def query_params(self) -> MappingABC[Mapping[str, Any]]:
        return DummyMapping(self.request.query_params)

    @property
    def path_params(self) -> dict[str, Any]:
        return self.request.path_params
