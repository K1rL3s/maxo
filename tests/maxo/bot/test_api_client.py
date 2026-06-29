import io
from http.cookies import SimpleCookie
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from multidict import CIMultiDict
from unihttp.http import HTTPResponse

from maxo.bot.api_client import MaxApiClient
from maxo.bot.methods.base import MaxoMethod
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
)
from maxo.types import AttachmentPayload

TOKEN = "f9LHod"  # noqa: S105


def mock_http_response(*chunks: bytes) -> MagicMock:
    mock_response = MagicMock()

    async def chunk_generator():
        for chunk in chunks:
            yield chunk

    mock_response.content.iter_chunked.return_value = chunk_generator()
    return mock_response


@pytest.fixture
async def api_client():
    client = MaxApiClient(
        token=TOKEN,
        request_dumper=lambda x: x,
        response_loader=lambda _, y: y,
    )
    yield client
    await client.close()


async def test_api_client_init(api_client: MaxApiClient):
    assert api_client._token == TOKEN
    assert "Authorization" in api_client._session.headers
    assert api_client._session.headers["Authorization"] == TOKEN
    assert "User-Agent" in api_client._session.headers


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
):
    response = HTTPResponse(
        status_code=status_code,
        data={},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method = MaxoMethod()
    with pytest.raises(error_class):
        api_client.handle_error(response, method)


async def test_validate_response_ok(api_client: MaxApiClient):
    response = HTTPResponse(
        status_code=200,
        data={"success": True},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method = MaxoMethod()
    api_client.validate_response(response, method)
    assert response.status_code == 200


async def test_validate_response_error(api_client: MaxApiClient):
    response = HTTPResponse(
        status_code=200,
        data={"success": False, "error_code": "some_error"},
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    method = MaxoMethod()
    api_client.validate_response(response, method)
    assert response.status_code == 400


async def test_download_to_binaryio(api_client: MaxApiClient):
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


async def test_download_to_path(api_client: MaxApiClient, tmp_path):
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


async def test_download_from_attachment_payload(api_client: MaxApiClient):
    mock_response = mock_http_response(b"test ", b"content")

    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_response
        mock_get.return_value = mock_context
        payload = AttachmentPayload(url="https://example.com/file")
        destination = io.BytesIO()
        await api_client.download(payload, destination=destination)

        assert destination.read() == b"test content"
