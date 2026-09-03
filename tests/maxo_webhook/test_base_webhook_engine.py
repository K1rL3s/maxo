import asyncio
from typing import Any

import pytest

from maxo import Bot
from maxo.routing.signals import MaxoUpdate
from maxo.serialization import get_retort
from maxo.transport.webhook.engines.base import BaseWebhookEngine
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.tasks import TaskTracker
from maxo.types import Updates
from maxo.types.binding import bind_bot
from tests.maxo_webhook.fixtures.web_request import (
    BlockingJsonWebRequest,
    DummyRequest,
    DummyWebRequest,
)
from tests.maxo_webhook.fixtures.webhook_engine import (
    CapturingAdapter,
    DummyDispatcher,
    DummyRoute,
)


class EngineProbe(BaseWebhookEngine[Any, Any, dict[str, Any]]):
    def __init__(
        self,
        dispatcher: DummyDispatcher,
        bot: Bot | None,
        *,
        web: CapturingAdapter,
    ) -> None:
        self.bot = bot
        self.task_tracker = TaskTracker()

        super().__init__(
            dispatcher,
            web=web,
            route=DummyRoute({"bot_token": "42:TEST"}),
        )

    async def _on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        return None

    async def _on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        return None

    async def _resolve_bot(self, route_params: RouteParams) -> Bot | None:
        return self.bot

    def _get_task_tracker(self, bot: Bot) -> TaskTracker:
        return self.task_tracker


@pytest.mark.asyncio
async def test_engine_acknowledges_empty_dispatcher_result(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)

    response = await engine.handle_request(update_request)

    assert response == {"kind": "json", "status_code": 200, "data": {}, "headers": None}


@pytest.mark.asyncio
async def test_engine_stops_accepting_requests_after_shutdown_starts(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)
    await engine.on_shutdown(None)

    response = await engine.handle_request(update_request)

    assert response == {
        "kind": "json",
        "status_code": 503,
        "data": {"detail": "Service unavailable"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None


@pytest.mark.asyncio
async def test_engine_accepts_requests_again_after_startup(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)
    await engine.on_shutdown(None)
    await engine.on_startup(None)

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)

    assert response == {"kind": "json", "status_code": 200, "data": {}, "headers": None}
    assert dispatcher.webhook_update == MaxoUpdate(
        update=bind_bot(get_retort().load(update_request.raw.json_data, Updates), bot),
    )


@pytest.mark.asyncio
async def test_engine_returns_not_found_when_bot_cannot_be_resolved(
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot=None, web=adapter)

    response = await engine.handle_request(update_request)

    assert response == {
        "kind": "json",
        "status_code": 404,
        "data": {"detail": "Not found"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None


@pytest.mark.asyncio
async def test_engine_returns_bad_request_when_json_payload_is_invalid(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)

    response = await engine.handle_request(
        DummyWebRequest(DummyRequest(json_error=ValueError("invalid json"))),
    )

    assert response == {
        "kind": "json",
        "status_code": 400,
        "data": {"detail": "Bad request"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None


@pytest.mark.asyncio
async def test_engine_lifespan_runs_startup_then_shutdown(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)

    await engine.on_startup(None)
    assert not engine._is_shutting_down
    response = await engine.handle_request(update_request)
    assert response["status_code"] == 200
    await engine.on_shutdown(None)

    assert engine._is_shutting_down
    response = await engine.handle_request(update_request)  # type: ignore[unreachable]
    assert response["status_code"] == 503


@pytest.mark.asyncio
async def test_engine_rejects_inflight_request_after_shutdown(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
    update_request: DummyWebRequest,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)
    request = BlockingJsonWebRequest(update_request.raw)
    request_task = asyncio.create_task(engine.handle_request(request))
    await request.json_started.wait()

    await engine.on_shutdown(None)
    request.json_continue.set()
    response = await request_task
    await asyncio.sleep(0)

    assert response["status_code"] == 503
    assert dispatcher.webhook_update is None
    assert engine.task_tracker._tasks == set()


@pytest.mark.asyncio
async def test_engine_returns_bad_request_for_schema_invalid_update(
    bot: Bot,
    adapter: CapturingAdapter,
    dispatcher: DummyDispatcher,
) -> None:
    engine = EngineProbe(dispatcher, bot, web=adapter)
    request = DummyWebRequest(
        DummyRequest(
            json_data={
                "update_type": "message_created",
                "message": "not-an-object",
            },
        ),
    )

    response = await engine.handle_request(request)

    assert response == {
        "kind": "json",
        "status_code": 400,
        "data": {"detail": "Bad request"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None
