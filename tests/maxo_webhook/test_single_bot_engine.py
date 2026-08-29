import asyncio

import pytest

from maxo import Bot
from maxo.routing.signals import MaxoUpdate
from maxo.transport.webhook.engines.single import SingleBotEngine
from maxo.transport.webhook.route import BotIdParam, Route
from tests.maxo_webhook.fixtures.shutdown import (
    BlockingDispatcher,
    BlockingShutdownDispatcher,
    SubscribingClient,
    TrackableClient,
)
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest
from tests.maxo_webhook.fixtures.webhook_engine import (
    CapturingAdapter,
    DummyDispatcher,
    DummyRoute,
)


@pytest.mark.asyncio
async def test_single_bot_engine_uses_configured_bot_instead_of_route_params(
    bot: Bot,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": "100:OTHER"}),
    )

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)

    assert response["status_code"] == 200
    assert dispatcher.webhook_bot is bot
    assert dispatcher.webhook_bot.token == bot_token
    assert isinstance(dispatcher.webhook_update, MaxoUpdate)
    assert dispatcher.webhook_update.update.message.body.text == "hello"
    assert dispatcher.webhook_update.update.message.body.mid == "msg-1"


@pytest.mark.asyncio
async def test_single_bot_engine_rejects_new_requests_once_shutdown_has_started(
    bot: Bot,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": "100:OTHER"}),
    )

    await engine.handle_request(update_request)
    await asyncio.sleep(0)
    assert dispatcher.started_updates == 1

    shutdown_task = asyncio.create_task(engine.on_shutdown(app=None))
    await asyncio.sleep(0)

    response = await engine.handle_request(
        DummyWebRequest(DummyRequest(json_data={"update_id": 2})),
    )

    dispatcher.release_updates.set()
    await shutdown_task

    assert response["status_code"] == 503
    assert dispatcher.started_updates == 1


@pytest.mark.asyncio
async def test_single_bot_engine_rejects_request_during_shutdown(
    bot: Bot,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),
    )

    shutdown_task = asyncio.create_task(engine.on_shutdown(None))
    await asyncio.wait_for(dispatcher.shutdown_started.wait(), timeout=1)

    try:
        response = await engine.handle_request(update_request)
    finally:
        dispatcher.release_shutdown.set()
        await asyncio.wait_for(shutdown_task, timeout=1)

    assert response["status_code"] == 503
    assert len(engine._task_tracker._tasks) == 0


@pytest.mark.asyncio
async def test_single_bot_engine_rejects_request_after_shutdown(
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    client = TrackableClient(bot_id=42)
    bot = Bot("42:TEST", client=client, warming_up=False)
    dispatcher = BlockingShutdownDispatcher()
    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=adapter,
        route=DummyRoute({"bot_token": bot.token}),
    )

    dispatcher.release_shutdown.set()
    await engine.on_shutdown(None)

    response = await engine.handle_request(update_request)

    # Клиент создали снаружи - бот его не закрывает, даже при shutdown.
    assert client.closed is False
    assert bot.closed is True
    assert response["status_code"] == 503


@pytest.mark.asyncio
async def test_single_bot_engine_subscribes_before_startup_with_bot_id_route(
    adapter: CapturingAdapter,
    bot_token: str,
) -> None:
    client = SubscribingClient(bot_id=42)
    bot = Bot(bot_token, client=client, warming_up=False)
    engine = SingleBotEngine(
        DummyDispatcher(),
        bot,
        web=adapter,
        route=Route(
            base_url="https://example.test",
            path="/webhook/{bot_id}",
            params={"bot_id": BotIdParam()},
        ),
    )

    await engine.subscribe()

    assert client.subscribed == ["https://example.test/webhook/42"]
