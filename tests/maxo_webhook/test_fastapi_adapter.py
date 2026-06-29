from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from maxo.transport.webhook.adapters.fastapi.adapter import (
    FastApiBoundRequest,
    FastApiWebAdapter,
)


@pytest.fixture
def app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def adapter() -> FastApiWebAdapter:
    return FastApiWebAdapter()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_bind(adapter: FastApiWebAdapter):
    request = Request(scope={"type": "http", "headers": [], "query_string": b""})
    bound_request = adapter.bind(request)
    assert isinstance(bound_request, FastApiBoundRequest)
    assert bound_request.request is request


def test_bound_request_no_client(adapter: FastApiWebAdapter):
    request = Request(
        scope={"type": "http", "headers": [], "query_string": b"", "client": None},
    )
    bound_request = adapter.bind(request)
    assert bound_request.client_ip is None


def test_create_json_response(adapter: FastApiWebAdapter):
    response = adapter.create_json_response(status=200, payload={"ok": True})
    assert response.status_code == 200
    assert response.body == b'{"ok":true}'


async def test_register_and_handle(
    app: FastAPI,
    adapter: FastApiWebAdapter,
    client: TestClient,
):
    handler_mock = AsyncMock(
        return_value=adapter.create_json_response(status=200, payload={"ok": True}),
    )

    async def handler(request: FastApiBoundRequest):
        return await handler_mock(request)

    adapter.register(app=app, path="/webhook", handler=handler)

    response = client.post("/webhook", json={"update_id": 1})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    handler_mock.assert_awaited_once()

    # Check bound request properties
    bound_request = handler_mock.call_args[0][0]
    assert isinstance(bound_request, FastApiBoundRequest)
    json_body = await bound_request.json()
    assert json_body == {"update_id": 1}
    assert bound_request.client_ip == "testclient"
    assert "user-agent" in bound_request.headers
    assert bound_request.headers["user-agent"] == "testclient"
    assert not bound_request.query_params
    assert not bound_request.path_params
