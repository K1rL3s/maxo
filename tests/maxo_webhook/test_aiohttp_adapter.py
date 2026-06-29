from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.web_app import Application

from maxo.transport.webhook.adapters.aiohttp.adapter import (
    AiohttpBoundRequest,
    AiohttpWebAdapter,
)


@pytest.fixture
def aiohttp_app() -> web.Application:
    return web.Application()


@pytest.fixture
def mocked_engine() -> MagicMock:
    engine = MagicMock()
    engine.feed_request = AsyncMock()
    return engine


@pytest.mark.asyncio
async def test_adapter(aiohttp_client: AiohttpClient, aiohttp_app: Application) -> None:
    payload = None

    async def handler(request: AiohttpBoundRequest) -> web.Response:
        nonlocal payload

        assert isinstance(request, AiohttpBoundRequest)
        payload = await request.json()
        return web.Response(status=200)

    engine = AsyncMock(side_effect=handler)

    adapter = AiohttpWebAdapter()
    adapter.register(aiohttp_app, "/webhook", engine)

    client = await aiohttp_client(aiohttp_app)
    response = await client.post("/webhook", json={"foo": "bar"})
    assert response.status == 200
    await response.read()

    engine.assert_awaited_once()
    request = engine.call_args.args[0]
    assert isinstance(request, AiohttpBoundRequest)
    assert payload == {"foo": "bar"}
