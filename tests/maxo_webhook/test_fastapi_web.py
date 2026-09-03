from typing import Any

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from maxo import Bot
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.web.base import WebRequest
from maxo.transport.webhook.web.fastapi import FastAPIAdapter
from tests.maxo_webhook.fixtures.webhook_engine import DummyDispatcher, SpyEngine


def test_fastapi_adapter_passes_bound_request_to_registered_post_handler() -> None:
    adapter = FastAPIAdapter()
    app = FastAPI()
    seen: dict[str, Any] = {}

    async def handler(request: WebRequest[Any]) -> Response:
        seen["raw"] = request.raw
        seen["client_ip"] = request.client_ip
        seen["header"] = request.headers["X-Test"]
        seen["query"] = request.query_params.getall("tag")
        seen["path"] = request.path_params["bot_token"]
        seen["json"] = await request.json()

        return adapter.json_response(
            status_code=202,
            data={"ok": "yes"},
            headers={"X-Reply": "done"},
        )

    async def on_startup(_app: Any) -> None:
        return None

    async def on_shutdown(_app: Any) -> None:
        return None

    adapter.register(
        app,
        "/webhook/{bot_token}",
        handler,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )

    with TestClient(app) as client:
        response = client.post(
            "/webhook/42:TEST?tag=first&tag=second",
            json={"update_id": 1},
            headers={"X-Test": "yes"},
        )

    assert response.status_code == 202
    assert response.headers["X-Reply"] == "done"
    assert response.json() == {"ok": "yes"}
    assert seen["raw"].path_params == {"bot_token": "42:TEST"}
    assert seen["client_ip"] == "testclient"
    assert seen["header"] == "yes"
    assert seen["query"] == ["first", "second"]
    assert seen["path"] == "42:TEST"
    assert seen["json"] == {"update_id": 1}


def test_fastapi_adapter_registers_lifecycle_callbacks_via_router(bot: Bot) -> None:
    events: list[Any] = []
    adapter = FastAPIAdapter()

    engine = SpyEngine(
        DummyDispatcher(),
        bot,
        events,
        web=adapter,
        route=Route(base_url="https://example.com", path="/webhook"),
    )

    app = FastAPI()
    engine.register(app)

    with TestClient(app) as client:
        assert events == [("engine_startup", app)]
        response = client.post(
            "/webhook",
            json={
                "update_type": "message_created",
                "timestamp": 1234567890,
                "message": {
                    "body": {"seq": 1, "mid": "msg-1", "text": "hello"},
                    "recipient": {"chat_id": 1, "chat_type": "dialog"},
                    "timestamp": 1234567890,
                },
            },
        )

    assert response.status_code == 200
    assert response.json() == {}
    assert events == [("engine_startup", app), ("engine_shutdown", app)]
