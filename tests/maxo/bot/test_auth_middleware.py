from collections.abc import AsyncIterator, Awaitable, Callable
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from unihttp.http import HTTPRequest, HTTPResponse, UploadFile
from unihttp.middlewares import AsyncHandler

from maxo.bot.api_client import MaxApiClient
from maxo.bot.methods import GetMyInfo
from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.bot.middlewares import AuthMiddleware
from maxo.serialization import create_retort
from tests.constants import TOKEN

AiohttpServer = Callable[[web.Application], Awaitable[TestServer]]
RecordingServer = tuple[TestServer, dict[str, str | None]]


def _request(url: str) -> HTTPRequest:
    return HTTPRequest(
        url=url,
        method="GET",
        header={},
        path={},
        query={},
        body={},
        file={},
        form=None,
    )


async def _handle(request: HTTPRequest) -> HTTPRequest:
    next_handler = AsyncMock()
    await AuthMiddleware(TOKEN).handle(request, next_handler)
    sent: HTTPRequest = next_handler.await_args_list[0].args[0]
    return sent


@pytest.mark.parametrize("url", ["messages", "/me", "chats/1/members"])
async def test_token_goes_to_api_paths(url: str) -> None:
    request = await _handle(_request(url))

    assert request.header["Authorization"] == TOKEN


@pytest.mark.parametrize(
    "url",
    [
        "https://fu.oneme.ru/api/upload.do?sig=1",
        "http://evil.test/file.bin",
        "//evil.test/file.bin",
    ],
)
async def test_token_never_goes_to_other_hosts(url: str) -> None:
    request = await _handle(_request(url))

    assert "Authorization" not in request.header


async def test_explicit_header_is_kept() -> None:
    request = _request("messages")
    request.header["Authorization"] = "other"

    sent = await _handle(request)

    assert sent.header["Authorization"] == "other"


async def test_api_client_middleware_ends_with_auth() -> None:
    retort = create_retort(warming_up=False)
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        middleware=[AsyncMock()],
    )
    try:
        assert isinstance(client.middleware[-1], AuthMiddleware)
    finally:
        await client.close()


@pytest.fixture
async def recording_server(
    aiohttp_server: AiohttpServer,
) -> RecordingServer:
    seen: dict[str, str | None] = {}

    async def record(request: web.Request) -> web.Response:
        seen[request.path] = request.headers.get("Authorization")
        if request.path == "/me":
            return web.json_response(
                {
                    "user_id": 1,
                    "is_bot": True,
                    "first_name": "Test",
                    "last_activity_time": 0,
                },
            )
        if request.path == "/upload":
            return web.json_response({"token": "file-token"})
        return web.Response(body=b"file")

    app = web.Application()
    app.router.add_route("*", "/{tail:.*}", record)
    server = await aiohttp_server(app)
    return server, seen


@pytest.fixture
async def server_client(
    recording_server: RecordingServer,
) -> AsyncIterator[MaxApiClient]:
    server, _ = recording_server
    retort = create_retort(warming_up=False)
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        base_url=str(server.make_url("/")),
    )
    yield client
    await client.close()


async def test_api_call_carries_token(
    recording_server: RecordingServer,
    server_client: MaxApiClient,
) -> None:
    _, seen = recording_server

    await server_client.call_method(GetMyInfo())

    assert seen["/me"] == TOKEN


async def test_download_goes_without_token(
    recording_server: RecordingServer,
    server_client: MaxApiClient,
) -> None:
    server, seen = recording_server

    result = await server_client.download(str(server.make_url("/file.bin")))

    assert result is not None
    assert result.read() == b"file"
    assert seen["/file.bin"] is None


async def test_upload_goes_without_token(
    recording_server: RecordingServer,
    server_client: MaxApiClient,
) -> None:
    server, seen = recording_server
    method = UploadMedia(
        upload_url=str(server.make_url("/upload")),
        file=UploadFile(file=b"video", filename="video.mp4"),
    )

    await server_client.call_method(method)

    assert seen["/upload"] is None


class _HeaderSpy:
    def __init__(self) -> None:
        self.header_after_call: dict[str, str] = {}

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse:
        response = await next_handler(request)
        self.header_after_call = dict(request.header)
        return response


async def test_outer_middleware_does_not_see_token(
    recording_server: RecordingServer,
) -> None:
    server, seen = recording_server
    spy = _HeaderSpy()
    retort = create_retort(warming_up=False)
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        base_url=str(server.make_url("/")),
        middleware=[spy],
    )
    try:
        await client.call_method(GetMyInfo())
    finally:
        await client.close()

    assert seen["/me"] == TOKEN
    assert "Authorization" not in spy.header_after_call
