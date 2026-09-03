import asyncio
from datetime import UTC, datetime
from typing import Any

from unihttp.clients.base import BaseAsyncClient
from unihttp.http.request import HTTPRequest
from unihttp.http.response import HTTPResponse
from unihttp.serializers.adaptix.serialize import DEFAULT_RETORT

from tests.maxo_webhook.fixtures.webhook_engine import DummyDispatcher


class BlockingShutdownDispatcher(DummyDispatcher):
    def __init__(self) -> None:
        super().__init__()
        self.shutdown_started = asyncio.Event()
        self.release_shutdown = asyncio.Event()

    async def _block_until_released(self) -> None:
        self.shutdown_started.set()
        await self.release_shutdown.wait()

    async def feed_signal(self, signal: Any, bot: Any = None) -> None:
        if type(signal).__name__ == "BeforeShutdown":
            await self._block_until_released()


class BlockingDispatcher(DummyDispatcher):
    """Test dispatcher that blocks update handling until released."""

    def __init__(self) -> None:
        super().__init__()
        self.started_updates = 0
        self.release_updates = asyncio.Event()

    async def feed_update(self, update: Any, bot: Any = None) -> Any:
        self.started_updates += 1
        self.webhook_bot = bot
        self.webhook_update = update
        await self.release_updates.wait()
        return self.result


class TrackableClient(BaseAsyncClient):
    """Fake unihttp client that answers GetMyInfo and tracks whether it was closed."""

    def __init__(self, bot_id: int = 42) -> None:
        super().__init__(
            base_url="",
            request_dumper=DEFAULT_RETORT,
            response_loader=DEFAULT_RETORT,
        )
        self.closed = False
        self._bot_id = bot_id
        self.seen_tokens: list[str | None] = []

    async def make_request(self, request: HTTPRequest) -> HTTPResponse[Any]:
        token = request.header.get("Authorization")
        self.seen_tokens.append(token)
        if request.url == "me":
            return HTTPResponse(
                status_code=200,
                headers={},
                data={
                    "user_id": int(token.split(":")[0]) if token else self._bot_id,
                    "first_name": "bot",
                    "username": "bot",
                    "is_bot": True,
                    "last_activity_time": datetime.now(UTC).isoformat(),
                },
                cookies={},
                raw_response=None,
            )
        raise NotImplementedError(f"TrackableClient can't answer {request.url!r}")

    async def close(self) -> None:
        self.closed = True


class SubscribingClient(TrackableClient):
    def __init__(self, bot_id: int = 42) -> None:
        super().__init__(bot_id=bot_id)
        self.subscribed: list[str] = []

    async def make_request(self, request: HTTPRequest) -> HTTPResponse[Any]:
        if request.url != "subscriptions":
            return await super().make_request(request)

        self.subscribed.append(request.body["url"])
        return HTTPResponse(
            status_code=200,
            headers={},
            data={"success": True},
            cookies={},
            raw_response=None,
        )
