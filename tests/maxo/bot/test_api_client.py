import io
from collections.abc import AsyncIterator
from http.cookies import SimpleCookie
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from adaptix import Retort
from aiohttp import ClientConnectionError, ClientSession
from multidict import CIMultiDict
from unihttp.clients.aiohttp import AiohttpAsyncClient
from unihttp.exceptions import NetworkError, RequestTimeoutError
from unihttp.http import HTTPResponse

from maxo.bot.api_client import MaxApiClient
from maxo.bot.methods import AddMembers  # type: ignore[deprecated]
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.middlewares import AttachmentNotReadyRetryMiddleware
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadGatewayError,
    MaxBotBadRequestError,
    MaxBotClientError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNetworkError,
    MaxBotNotFoundError,
    MaxBotServerError,
    MaxBotServiceUnavailableError,
    MaxBotTimeoutError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
    MaxoError,
)
from maxo.types import AttachmentPayload
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile
from tests.constants import TOKEN


def mock_http_response(*chunks: bytes) -> MagicMock:
    mock_response = MagicMock()

    async def chunk_generator() -> AsyncIterator[bytes]:
        for chunk in chunks:
            yield chunk

    mock_response.content.iter_chunked.return_value = chunk_generator()
    return mock_response


@pytest.fixture
async def api_client() -> AsyncIterator[MaxApiClient]:
    retort = Retort()
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
    )
    yield client
    await client.close()


async def test_api_client_init(api_client: MaxApiClient) -> None:
    assert api_client._token == TOKEN
    assert "Authorization" in api_client._session.headers
    assert api_client._session.headers["Authorization"] == TOKEN
    assert "User-Agent" in api_client._session.headers


async def test_api_client_registers_attachment_retry_middleware(
    api_client: MaxApiClient,
) -> None:
    assert isinstance(
        api_client.middleware[-1],
        AttachmentNotReadyRetryMiddleware,
    )


async def test_api_client_keeps_user_middleware_outer() -> None:
    user_middleware = MagicMock()
    retort = Retort()
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        middleware=[user_middleware],
    )
    try:
        assert client.middleware[0] is user_middleware
        assert isinstance(client.middleware[-1], AttachmentNotReadyRetryMiddleware)
    finally:
        await client.close()


async def test_upload_resumable_closes_dedicated_session(
    api_client: MaxApiClient,
) -> None:
    session = AsyncMock()
    result = UploadMediaResult(token="upload-token")  # noqa: S106
    file = BufferedInputFile.file(b"payload", "f.bin")

    with (
        patch.object(api_client, "_new_upload_session", return_value=session),
        patch(
            "maxo.bot.api_client.resumable_upload",
            new_callable=AsyncMock,
            return_value=result,
        ) as upload_mock,
    ):
        assert await api_client.upload_resumable("https://example.com", file) is result

    upload_mock.assert_awaited_once_with(
        url="https://example.com",
        file=file,
        session=session,
        response_loader=api_client.response_loader,
        json_loads=api_client.json_loads,
        config=api_client._upload_config,
        size=None,
    )
    session.close.assert_awaited_once()


async def test_ssl_context_is_lazy_with_custom_session() -> None:
    retort = Retort()
    session = ClientSession()
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=retort,
        response_loader=retort,
        session=session,
    )
    try:
        assert client._ssl_context is None
        first = client._get_ssl_context()
        second = client._get_ssl_context()
        assert first is second
    finally:
        await client.close()


@pytest.mark.parametrize(
    ("raised", "expected"),
    [
        (RequestTimeoutError("slow"), MaxBotTimeoutError),
        (NetworkError("dns"), MaxBotNetworkError),
        (ClientConnectionError("refused"), MaxBotNetworkError),
        (TimeoutError("timed out"), MaxBotTimeoutError),
    ],
)
async def test_make_request_wraps_transport_errors(
    api_client: MaxApiClient,
    raised: Exception,
    expected: type[MaxBotNetworkError],
) -> None:
    request = MagicMock()

    with (
        patch.object(
            AiohttpAsyncClient,
            "make_request",
            new_callable=AsyncMock,
            side_effect=raised,
        ),
        pytest.raises(expected) as exc_info,
    ):
        await api_client.make_request(request)

    # Наружу торчит только maxo-ошибка, исходная лежит в __cause__.
    assert isinstance(exc_info.value, MaxoError)
    assert exc_info.value.__cause__ is raised


async def test_make_request_passes_response_through(
    api_client: MaxApiClient,
) -> None:
    response = MagicMock()

    with patch.object(
        AiohttpAsyncClient,
        "make_request",
        new_callable=AsyncMock,
        return_value=response,
    ):
        assert await api_client.make_request(MagicMock()) is response


async def test_new_upload_session_uses_dedicated_connector(
    api_client: MaxApiClient,
) -> None:
    session = api_client._new_upload_session()
    try:
        assert session.connector is not None
        assert session.connector.limit == 1
        assert session.headers["Authorization"] == TOKEN
        assert "User-Agent" in session.headers
    finally:
        await session.close()


@pytest.mark.parametrize(
    (
        "status_code",
        "error_class",
    ),
    [
        (400, MaxBotBadRequestError),
        (401, MaxBotUnauthorizedError),
        (403, MaxBotForbiddenError),
        (404, MaxBotNotFoundError),
        (405, MaxBotMethodNotAllowedError),
        (415, MaxBotUnsupportedMediaTypeError),
        (429, MaxBotTooManyRequestsError),
        (500, MaxBotUnknownServerError),
        (502, MaxBotApiError),
        (503, MaxBotServiceUnavailableError),
    ],
)
async def test_handle_error(
    api_client: MaxApiClient,
    status_code: int,
    error_class: type[MaxBotApiError],
) -> None:
    response = HTTPResponse(
        status_code=status_code,
        data={},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    with pytest.raises(error_class):
        api_client.handle_error(response, method)


async def test_handle_error_with_non_dict_payload(api_client: MaxApiClient) -> None:
    response = HTTPResponse(
        status_code=502,
        data="plain error",
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    with pytest.raises(MaxBotApiError) as exc_info:
        api_client.handle_error(response, MaxoMethod())

    assert exc_info.value.raw_data == "plain error"


async def test_handle_error_converts_none_message(api_client: MaxApiClient) -> None:
    response = HTTPResponse(
        status_code=400,
        data={"message": None},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        api_client.handle_error(response, MaxoMethod())

    assert exc_info.value.message == ""


def test_api_error_str_uses_fields_and_raw_data() -> None:
    error = MaxBotApiError("code", "error", "message")
    raw_error = MaxBotApiError("", "", "", {"raw": "data"})

    assert str(error) == (
        "MaxBotApiError(code='code', error='error', message='message')"
    )
    assert str(raw_error) == "MaxBotApiError(raw_data={'raw': 'data'})"


async def test_validate_response_ok(api_client: MaxApiClient) -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": True},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    api_client.validate_response(response, method)
    assert response.status_code == 200


async def test_validate_response_error(api_client: MaxApiClient) -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": False, "error_code": "some_error"},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method: MaxoMethod[object] = MaxoMethod()
    api_client.validate_response(response, method)
    assert response.status_code == 400


async def test_validate_response_preserves_add_members_result(
    api_client: MaxApiClient,
) -> None:
    response = HTTPResponse(
        status_code=200,
        data={"success": False, "error_code": "some_error"},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    api_client.validate_response(
        response,
        AddMembers(chat_id=1, user_ids=[2]),
    )

    assert response.status_code == 200


async def test_download_to_binaryio(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context

        destination = io.BytesIO()
        result = await api_client.download(
            "https://example.com/file",
            destination=destination,
        )

        assert result is destination
        assert destination.read() == b"test content"
        mock_get.assert_called_once()


async def test_download_to_memory_by_default(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test")

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context

        result = await api_client.download("https://example.com/file")

    assert result is not None
    assert result.read() == b"test"


async def test_download_to_path(api_client: MaxApiClient, tmp_path: Path) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context

        file_path = tmp_path / "test_file.txt"
        result = await api_client.download(
            "https://example.com/file",
            destination=file_path,
        )

        assert result is None
        assert file_path.read_bytes() == b"test content"


async def test_download_from_attachment_payload(api_client: MaxApiClient) -> None:
    mock_response = mock_http_response(b"test ", b"content")

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        payload = AttachmentPayload(url="https://example.com/file")
        destination = io.BytesIO()
        await api_client.download(payload, destination=destination)

        assert destination.read() == b"test content"


@pytest.mark.parametrize(
    ("status_code", "error_class"),
    [
        (400, MaxBotBadRequestError),
        (401, MaxBotUnauthorizedError),
        (403, MaxBotForbiddenError),
        (404, MaxBotNotFoundError),
        (405, MaxBotMethodNotAllowedError),
        (415, MaxBotUnsupportedMediaTypeError),
        (429, MaxBotTooManyRequestsError),
        (500, MaxBotUnknownServerError),
        (502, MaxBotBadGatewayError),
        (503, MaxBotServiceUnavailableError),
        (418, MaxBotClientError),
        (501, MaxBotServerError),
        (302, MaxBotApiError),
    ],
)
async def test_handle_error_falls_back_to_status_group(
    api_client: MaxApiClient,
    status_code: int,
    error_class: type[MaxBotApiError],
) -> None:
    response = HTTPResponse(
        status_code=status_code,
        data={},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

    with pytest.raises(error_class):
        api_client.handle_error(response, MaxoMethod())
