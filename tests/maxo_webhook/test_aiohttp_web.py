import json
from typing import Any
from unittest.mock import Mock

from aiohttp.test_utils import make_mocked_request
from aiohttp.web import Application, Response

from maxo.transport.webhook.web.aiohttp import AiohttpAdapter


def test_aiohttp_adapter_exposes_framework_request_data() -> None:
    transport = Mock()
    transport.get_extra_info.return_value = ("127.0.0.1", 12345)
    raw_request = make_mocked_request(
        "POST",
        "/webhook/42:TEST?tag=first&tag=second",
        headers={"X-Test": "yes"},
        match_info={"bot_token": "42:TEST"},
        transport=transport,
    )

    request = AiohttpAdapter().bind_request(raw_request)

    assert request.raw is raw_request
    assert request.client_ip == "127.0.0.1"
    assert request.headers["X-Test"] == "yes"
    assert request.query_params.getall("tag") == ["first", "second"]
    assert request.path_params["bot_token"] == "42:TEST"  # noqa: S105


def test_aiohttp_adapter_registers_post_route_and_lifecycle_callbacks() -> None:
    adapter = AiohttpAdapter()
    app = Application()

    async def handler(_request: Any) -> Response:
        return adapter.json_response(status_code=200, data={"ok": "yes"})

    async def on_startup(_app: Any) -> None:
        return None

    async def on_shutdown(_app: Any) -> None:
        return None

    adapter.register(
        app,
        "/webhook",
        handler,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )

    routes = list(app.router.routes())
    assert len(routes) == 1
    assert routes[0].method == "POST"
    assert routes[0].resource is not None
    assert routes[0].resource.canonical == "/webhook"
    assert app.on_startup[-1] is on_startup
    assert app.on_shutdown[-1] is on_shutdown


def test_aiohttp_adapter_builds_json_response_with_status_and_headers() -> None:
    response = AiohttpAdapter().json_response(
        status_code=418,
        data={"detail": "teapot"},
        headers={"X-Test": "yes"},
    )

    assert response.status == 418
    assert response.headers["X-Test"] == "yes"
    assert response.content_type == "application/json"
    assert response.text is not None
    assert json.loads(response.text) == {"detail": "teapot"}
