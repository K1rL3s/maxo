import asyncio
from typing import Any

import pytest
from unihttp.http.request import HTTPRequest
from unihttp.http.response import HTTPResponse

from maxo import Bot
from maxo.transport.webhook.configs.bot import BotConfig
from maxo.transport.webhook.engines.token import TokenEngine
from tests.maxo_webhook.fixtures.shutdown import (
    BlockingShutdownDispatcher,
    TrackableClient,
)
from tests.maxo_webhook.fixtures.web_request import DummyWebRequest
from tests.maxo_webhook.fixtures.webhook_engine import (
    CapturingAdapter,
    DummyDispatcher,
    DummyRoute,
)


class SubscriptionsClient(TrackableClient):
    """TrackableClient that also answers `subscriptions` and records those calls."""

    def __init__(self, bot_id: int = 42) -> None:
        super().__init__(bot_id=bot_id)
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []

    fail_subscribe = False
    fail_unsubscribe = False

    async def make_request(self, request: HTTPRequest) -> HTTPResponse[Any]:
        if request.url != "subscriptions":
            return await super().make_request(request)

        if request.method.lower() == "post" and self.fail_subscribe:
            raise ConnectionError("subscribe failed")

        if request.method.lower() == "delete":
            if self.fail_unsubscribe:
                raise ConnectionError("unsubscribe failed")
            self.unsubscribed.append(request.query["url"])
        else:
            self.subscribed.append(request.body["url"])

        return HTTPResponse(
            status_code=200,
            headers={},
            data={"success": True},
            cookies={},
            raw_response=None,
        )


@pytest.mark.asyncio
async def test_token_webhook_engine_does_not_register_bot_when_subscribe_fails(
    bot_token: str,
    adapter: CapturingAdapter,
) -> None:
    # TrackableClient only answers `me`, so subscribe blows up.
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=TrackableClient()),
    )

    with pytest.raises(NotImplementedError):
        await engine.add_bot(bot_token)

    assert engine.bots == {}
    assert engine._token_ids == {}


@pytest.mark.asyncio
async def test_token_webhook_engine_replaces_bot_with_same_token_without_unsubscribing(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
) -> None:
    client = SubscriptionsClient(bot_id=bot_id)
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=client),
    )

    first = await engine.add_bot(bot_token)
    second = await engine.add_bot(bot_token)

    url = f"https://example.test/webhook/{bot_token}"
    assert client.subscribed == [url, url]
    # Same URL as the fresh subscription - unsubscribing would have killed it.
    assert client.unsubscribed == []
    assert engine.bots == {bot_id: second}
    assert second is not first
    assert engine._token_ids == {bot_token: bot_id}


@pytest.mark.asyncio
async def test_token_webhook_engine_keeps_working_bot_when_re_add_fails(
    bot_id: int,
    adapter: CapturingAdapter,
) -> None:
    old_token, new_token = f"{bot_id}:OLD", f"{bot_id}:NEW"
    client = SubscriptionsClient(bot_id=bot_id)
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),  # ty:ignore[invalid-argument-type]
        bot_config=BotConfig(client=client),
    )

    first = await engine.add_bot(old_token)
    client.fail_subscribe = True

    with pytest.raises(ConnectionError):
        await engine.add_bot(new_token)

    assert engine.bots == {bot_id: first}
    assert engine._token_ids == {old_token: bot_id}
    assert client.unsubscribed == []


@pytest.mark.asyncio
async def test_token_engine_keeps_old_bot_when_unsubscribe_fails(
    bot_id: int,
    adapter: CapturingAdapter,
) -> None:
    old_token, new_token = f"{bot_id}:OLD", f"{bot_id}:NEW"
    client = SubscriptionsClient(bot_id=bot_id)
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),
        bot_config=BotConfig(client=client),
    )

    old = await engine.add_bot(old_token)
    client.fail_unsubscribe = True

    with pytest.raises(ConnectionError):
        await engine.add_bot(new_token)

    assert engine.bots == {bot_id: old}
    assert engine._token_ids == {old_token: bot_id}
    assert not old.closed


@pytest.mark.asyncio
async def test_token_webhook_engine_unsubscribes_old_url_when_token_changes(
    bot_id: int,
    adapter: CapturingAdapter,
) -> None:
    # TrackableClient derives the bot id from the token prefix, so both tokens
    # resolve to the same bot with different webhook URLs.
    old_token, new_token = f"{bot_id}:OLD", f"{bot_id}:NEW"
    client = SubscriptionsClient(bot_id=bot_id)
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),
        bot_config=BotConfig(client=client),
    )

    await engine.add_bot(old_token)
    bot = await engine.add_bot(new_token)

    old_url = f"https://example.test/webhook/{old_token}"
    new_url = f"https://example.test/webhook/{new_token}"
    assert client.subscribed == [old_url, new_url]
    assert client.unsubscribed == [old_url]
    assert engine.bots == {bot_id: bot}
    assert engine._token_ids == {new_token: bot_id}


@pytest.mark.asyncio
async def test_token_webhook_engine_dispatches_to_bot_resolved_from_route_token(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    client = TrackableClient(bot_id=bot_id)
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute({"bot_token": bot_token}),
        bot_config=BotConfig(client=client),
    )

    response = await engine.handle_request(update_request)
    await asyncio.sleep(0)

    assert response["status_code"] == 200
    assert dispatcher.webhook_bot is engine.bots[bot_id]
    assert dispatcher.webhook_bot.token == bot_token
    assert dispatcher.webhook_update is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "route_params",
    [
        {},
        {"bot_token": ""},
    ],
    ids=["missing", "empty"],
)
async def test_token_webhook_engine_returns_not_found_when_route_token_is_missing_or_empty(
    adapter: CapturingAdapter,
    route_params: dict[str, str],
    update_request: DummyWebRequest,
) -> None:
    dispatcher = DummyDispatcher()
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute(route_params),
        bot_config=BotConfig(client=TrackableClient()),
    )

    response = await engine.handle_request(update_request)

    assert response == {
        "kind": "json",
        "status_code": 404,
        "data": {"detail": "Not found"},
        "headers": None,
    }
    assert dispatcher.webhook_update is None
    assert engine.bots == {}


@pytest.mark.asyncio
async def test_token_engine_rejects_request_during_shutdown_without_creating_bot(
    bot_id: int,
    bot_token: str,
    adapter: CapturingAdapter,
    update_request: DummyWebRequest,
) -> None:
    dispatcher = BlockingShutdownDispatcher()
    client = TrackableClient(bot_id=bot_id)
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute({"bot_token": bot_token}),
        bot_config=BotConfig(client=client),
    )

    shutdown_task = asyncio.create_task(engine.on_shutdown(None))
    await asyncio.wait_for(dispatcher.shutdown_started.wait(), timeout=1)

    try:
        response = await engine.handle_request(update_request)
    finally:
        dispatcher.release_shutdown.set()
        await asyncio.wait_for(shutdown_task, timeout=1)

    assert response["status_code"] == 503
    assert bot_id not in engine.bots
    assert bot_id not in engine._task_trackers


class SignalCallbackDispatcher(DummyDispatcher):
    """Runs an async callback when a signal of the given type fires."""

    def __init__(self, callbacks: dict[str, Any]) -> None:
        super().__init__()
        self._callbacks = callbacks

    async def feed_signal(self, signal: Any, bot: Bot | None = None) -> None:
        callback = self._callbacks.get(type(signal).__name__)
        if callback is not None:
            await callback()


@pytest.mark.asyncio
async def test_token_webhook_engine_keeps_bot_added_during_after_shutdown(
    bot_id: int,
    adapter: CapturingAdapter,
) -> None:
    late_id = bot_id + 1
    late_token = f"{late_id}:LATE"
    client = SubscriptionsClient(bot_id=late_id)

    async def add_bot_from_after_shutdown() -> None:
        await engine.add_bot(late_token)

    dispatcher = SignalCallbackDispatcher(
        {"AfterShutdown": add_bot_from_after_shutdown},
    )
    engine = TokenEngine(
        dispatcher,
        web=adapter,
        route=DummyRoute(),
        bot_config=BotConfig(client=client),
    )

    await engine.on_shutdown(None)

    assert late_id in engine.bots
    assert engine._token_ids.get(late_token) == late_id


class BlockingFirstInfoClient(SubscriptionsClient):
    """Blocks the FIRST `get_my_info()` call so a second, faster resolution
    of a different token for the same bot can race ahead of it."""

    def __init__(self, bot_id: int) -> None:
        super().__init__(bot_id=bot_id)
        self.info_calls = 0
        self.first_info_started = asyncio.Event()
        self.release_first_info = asyncio.Event()

    async def make_request(self, request: HTTPRequest) -> HTTPResponse[Any]:
        if request.url == "me":
            self.info_calls += 1
            if self.info_calls == 1:
                self.first_info_started.set()
                await self.release_first_info.wait()
        return await super().make_request(request)


@pytest.mark.asyncio
async def test_token_engine_serializes_concurrent_bot_resolution(
    bot_id: int,
    adapter: CapturingAdapter,
) -> None:
    """
    Без `_bots_lock` более медленная резолюция токена побеждает и вытесняет более свежую.
    `_bots_lock` сериализует `_resolve_bot`, так что вторая резолюция ждёт первую целиком
    """

    client = BlockingFirstInfoClient(bot_id)
    engine = TokenEngine(
        DummyDispatcher(),
        web=adapter,
        route=DummyRoute(),
        bot_config=BotConfig(client=client),
    )
    first_task = asyncio.create_task(
        engine._resolve_bot({"bot_token": f"{bot_id}:OLD"}),
    )
    await client.first_info_started.wait()
    second_task = asyncio.create_task(
        engine._resolve_bot({"bot_token": f"{bot_id}:NEW"}),
    )
    await asyncio.sleep(0)

    # лок держит второй resolve перед стартом, пока первый не отпустят
    assert client.info_calls == 1
    client.release_first_info.set()
    first, second = await asyncio.gather(first_task, second_task)

    assert first is not None
    assert second is not None
    assert first.closed
    assert engine.bots == {bot_id: second}
    await engine.on_shutdown(None)
    assert second.closed
