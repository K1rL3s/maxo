from collections.abc import AsyncGenerator, Iterable
from functools import partial
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import unquote

import pytest
from unihttp.exceptions import NetworkError as UnihttpNetworkError

from maxo.backoff import BackoffConfig
from maxo.bot import Bot
from maxo.bot.media import Media
from maxo.bot.methods.upload.chunk_upload import ChunkUpload, UploadResponseBody
from maxo.bot.upload import ProcessingConfig, UploadConfig, UploadMethod
from maxo.enums import UploadType
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotNetworkError,
    MaxBotServerError,
    MaxBotTimeoutError,
    MaxBotTooManyRequestsError,
    MaxBotUnsupportedMediaTypeError,
    MaxoError,
)
from maxo.serialization import get_retort
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile, InputFile
from tests.factories import make_bot as make_base_bot

_MIB = 1024 * 1024
_URL = "https://upload.example/upload.do"
_FAST_BACKOFF = BackoffConfig(min_delay=0.0, max_delay=0.001, factor=2.0, jitter=0.0)


class _FakeResponse:
    """`data` - как его уже отдал бы `AiohttpAsyncClient.make_request`: JSON
    распарсен в dict/list, а нераспарсиваемое тело осталось raw-байтами."""

    def __init__(self, status_code: int, data: UploadResponseBody) -> None:
        self.status_code = status_code
        self.data = data


def _answer(method: ChunkUpload, item: _FakeResponse | Exception) -> _FakeResponse:
    """Like unihttp: transport errors propagate, status >= 400 calls
    `method.on_error`."""
    if isinstance(item, Exception):
        raise item
    if item.status_code >= 400:
        # Duck-typed response: `on_error` reads only status and data
        method.on_error(item)  # type: ignore[arg-type]
    return item


class _FakeClient:
    """Upload client: returns canned responses and records requests.
    Per-call `middleware` is ignored; retries are covered by `_ChainClient`
    and `test_chunk_upload_retry_middleware.py`."""

    def __init__(self, responses: Iterable[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def call_method(
        self,
        method: ChunkUpload,
        *,
        middleware: Any = None,
    ) -> UploadResponseBody:
        self.calls.append(
            {
                "url": method.upload_url,
                "data": method.chunk,
                "headers": {
                    "content-range": method.content_range,
                    "content-disposition": method.content_disposition,
                },
            },
        )
        return _answer(method, self._responses.pop(0)).data

    async def close(self) -> None:
        self.closed = True


class _ChainClient:
    """Like `_FakeClient`, but runs the per-call middleware chain."""

    def __init__(self, responses: Iterable[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.attempts = 0

    async def call_method(
        self,
        method: ChunkUpload,
        *,
        middleware: Any = None,
    ) -> UploadResponseBody:
        async def terminal(request: Any) -> _FakeResponse:
            self.attempts += 1
            return _answer(method, self._responses.pop(0))

        handler = terminal
        for m in reversed(list(middleware or ())):
            handler = partial(m.handle, next_handler=handler)
        response = await handler(MagicMock())
        return response.data

    async def close(self) -> None:
        pass


def make_bot(
    client: Any,
    upload_config: UploadConfig | None = None,
    **kwargs: Any,
) -> Bot:
    """Bot whose file-host requests go through `client`."""
    return make_base_bot(media=Media(client, upload_config), **kwargs)


async def _upload(
    client: Any,
    file: InputFile | None = None,
    config: UploadConfig | None = None,
    **kwargs: Any,
) -> UploadMediaResult | None:
    file = file or BufferedInputFile.video(b"hello", "f.bin")
    if "size" not in kwargs:
        kwargs["size"] = await file.size()
    return await make_bot(client, config).media._upload_resumable(_URL, file, **kwargs)


async def test_sends_chunks_with_correct_content_range() -> None:
    client = _FakeClient(
        [
            _FakeResponse(201, b"0-3/10"),
            _FakeResponse(201, b"0-7/10"),
            _FakeResponse(200, {"token": "tok"}),
        ],
    )

    result = await _upload(
        client,
        BufferedInputFile.video(b"abcdefghij", "f.bin"),
        UploadConfig(chunk_size=4),
    )

    assert isinstance(result, UploadMediaResult)
    assert result.token == "tok"  # noqa: S105
    ranges = [call["headers"]["content-range"] for call in client.calls]
    assert ranges == ["bytes 0-3/10", "bytes 4-7/10", "bytes 8-9/10"]
    assert [call["data"] for call in client.calls] == [b"abcd", b"efgh", b"ij"]
    assert 'filename="f.bin"' in client.calls[0]["headers"]["content-disposition"]


async def test_single_chunk_small_file() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])

    result = await _upload(client)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert client.calls[0]["headers"]["content-range"] == "bytes 0-4/5"


@pytest.mark.parametrize("body", [b"0-4/5", ["0-4/5"]])
async def test_non_dict_final_body_returns_none(body: UploadResponseBody) -> None:
    assert await _upload(_FakeClient([_FakeResponse(200, body)])) is None


async def test_content_disposition_is_latin1_safe() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])
    file_name = 'файл "1".bin'

    await _upload(client, BufferedInputFile.video(b"hello", file_name))

    disposition = client.calls[0]["headers"]["content-disposition"]
    disposition.encode("latin-1")
    encoded = disposition.removeprefix('attachment; filename="').removesuffix('"')
    assert unquote(encoded) == file_name


class _TrackingInputFile(InputFile):
    """Отдаёт 10 байт кусками и запоминает, закрыли ли поток."""

    def __init__(self) -> None:
        self.closed = False

    @property
    def file_name(self) -> str:
        return "f.bin"

    @property
    def type(self) -> UploadType:
        return UploadType.VIDEO

    async def read(self) -> bytes:
        return b"abcdefghij"

    async def stream(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        try:
            data = b"abcdefghij"
            for i in range(0, len(data), chunk_size):
                yield data[i : i + chunk_size]
        finally:
            self.closed = True


async def test_stream_is_closed_when_chunk_fails() -> None:
    client = _FakeClient([_FakeResponse(400, b"nope")])
    file = _TrackingInputFile()

    with pytest.raises(MaxBotApiError):
        await _upload(client, file, UploadConfig(chunk_size=4))

    assert file.closed is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"chunk_size": 0},
        {"chunk_retries": -1},
        {"resumable_threshold": -1},
    ],
)
def test_upload_config_rejects_invalid_values(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="should"):
        UploadConfig(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"not_ready_max_retries": -1},
        {"base_delay": -1},
        {"delay_per_mib": -1},
        {"max_delay": -1},
    ],
)
def test_processing_config_rejects_invalid_values(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="should"):
        ProcessingConfig(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("body", "message"),
    [(b"plain error", "plain error"), (["plain error"], "['plain error']")],
)
async def test_non_dict_error_status_raises_base_error(
    body: UploadResponseBody,
    message: str,
) -> None:
    with pytest.raises(MaxBotApiError) as exc_info:
        await _upload(_FakeClient([_FakeResponse(406, body)]))

    error = exc_info.value
    assert error.status_code == 406
    assert error.error == ""
    assert error.message == message
    assert error.raw_data == body


@pytest.mark.parametrize(
    ("status", "error_class"),
    [
        (400, MaxBotBadRequestError),
        (415, MaxBotUnsupportedMediaTypeError),
        (429, MaxBotTooManyRequestsError),
    ],
)
async def test_client_error_status_preserves_typed_api_error(
    status: int,
    error_class: type[MaxBotApiError],
) -> None:
    payload = {
        "error_code": "proto.payload",
        "error_data": "attachment.not.ready",
        "message": "cannot process attachment",
    }
    client = _FakeClient([_FakeResponse(status, payload)])

    with pytest.raises(error_class) as exc_info:
        await _upload(client)

    error = exc_info.value
    assert error.code == "proto.payload"
    assert error.error == "attachment.not.ready"
    assert error.message == "cannot process attachment"
    assert error.raw_data == payload
    assert len(client.calls) == 1


async def test_server_error_status_raises_immediately() -> None:
    # 5xx retries live in `ChunkUploadRetryMiddleware`; here `_upload_resumable`
    # itself must not retry, and the error type follows the status.
    client = _FakeClient([_FakeResponse(502, b"<html>Bad Gateway</html>")])

    with pytest.raises(MaxBotServerError) as exc_info:
        await _upload(client)

    assert exc_info.value.status_code == 502
    assert len(client.calls) == 1


async def test_network_error_propagates_without_retry() -> None:
    client = _FakeClient([MaxBotNetworkError("boom")])

    with pytest.raises(MaxBotNetworkError, match="boom"):
        await _upload(client)

    assert len(client.calls) == 1


async def test_non_json_server_error_is_retried() -> None:
    """A proxy 502 comes as an HTML page, not JSON, and is still retried."""
    client = _ChainClient(
        [
            _FakeResponse(502, b"<html>Bad Gateway</html>"),
            _FakeResponse(200, {"token": "tok"}),
        ],
    )

    result = await _upload(client, config=UploadConfig(chunk_backoff=_FAST_BACKOFF))

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert client.attempts == 2


async def test_chunk_retries_apply_to_raw_transport_errors() -> None:
    client = _ChainClient([UnihttpNetworkError("boom") for _ in range(3)])
    config = UploadConfig(chunk_retries=2, chunk_backoff=_FAST_BACKOFF)

    with pytest.raises(MaxBotNetworkError):
        await _upload(client, config=config)

    assert client.attempts == 3


async def test_chunks_go_through_the_given_media_client() -> None:
    """Chunks go through the given `Media` client (e.g. with its own proxy),
    not the API client or a hidden one."""
    api = AsyncMock()
    client = _FakeClient([_FakeResponse(200, b"0-4/5")])
    bot = make_base_bot(client=api, media=Media(cast("Any", client)))

    await bot.media._upload_resumable(
        _URL,
        BufferedInputFile.video(b"hello", "v.mp4"),
        size=5,
    )

    assert len(client.calls) == 1
    assert client.closed is False
    api.call_method.assert_not_awaited()


def test_chunk_asks_for_parallel_mode() -> None:
    request = ChunkUpload(
        upload_url=_URL,
        content_range="bytes 0-4/5",
        content_disposition='attachment; filename="v.mp4"',
        chunk=b"hello",
    ).build_http_request(get_retort())

    assert request.url == _URL
    assert request.raw == b"hello"
    assert request.header == {
        "content-range": "bytes 0-4/5",
        "content-disposition": 'attachment; filename="v.mp4"',
        "content-type": "application/octet-stream",
        "x-uploading-mode": "parallel",
    }


async def test_network_error_is_a_maxo_error() -> None:
    # Ловить сетевые сбои можно одним `except MaxoError`.
    assert issubclass(MaxBotNetworkError, MaxoError)
    assert issubclass(MaxBotTimeoutError, MaxBotNetworkError)


async def test_size_mismatch_raises() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])

    # Файл «усох» между замером размера и стримом.
    with pytest.raises(ValueError, match="изменился во время загрузки"):
        await _upload(client, size=999)


def test_should_use_resumable_respects_explicit_method() -> None:
    resumable = UploadConfig(method=UploadMethod.RESUMABLE)
    single = UploadConfig(method=UploadMethod.SINGLE)

    assert resumable.should_use_resumable(UploadType.VIDEO, 1) is True
    assert single.should_use_resumable(UploadType.VIDEO, 10**9) is False


def test_should_use_resumable_auto_by_threshold() -> None:
    config = UploadConfig(method=UploadMethod.AUTO, resumable_threshold=100)
    assert config.should_use_resumable(UploadType.VIDEO, 99) is False
    assert config.should_use_resumable(UploadType.VIDEO, 100) is True


def test_default_everyday_files_stay_single() -> None:
    # Обычные загрузки (фото, документы, короткие видео) должны идти тем же
    # single-путём, что и до появления resumable, - без заметной разницы
    config = UploadConfig()
    threshold = config.resumable_threshold
    assert config.should_use_resumable(UploadType.VIDEO, 1 * _MIB) is False
    assert config.should_use_resumable(UploadType.VIDEO, threshold - 1) is False


def test_default_chunk_equals_threshold_so_boundary_is_one_request() -> None:
    # Файл ровно на пороге уходит одним куском - тем же одним запросом,
    # как прежний single-аплоад - переход в resumable незаметен
    config = UploadConfig()
    threshold = config.resumable_threshold
    assert config.chunk_size == threshold
    assert config.should_use_resumable(UploadType.VIDEO, threshold) is True
    assert -(-threshold // config.chunk_size) == 1


@pytest.mark.parametrize("upload_type", [UploadType.IMAGE, UploadType.VIDEO])
def test_estimated_delay_zero_for_instant_types(upload_type: UploadType) -> None:
    assert ProcessingConfig().estimated_delay(upload_type, 100 * _MIB) == 0.0


@pytest.mark.parametrize("upload_type", [UploadType.FILE, UploadType.AUDIO])
def test_estimated_delay_grows_with_size(upload_type: UploadType) -> None:
    config = ProcessingConfig()
    small = config.estimated_delay(upload_type, 1 * _MIB)
    big = config.estimated_delay(upload_type, 100 * _MIB)

    assert small >= config.base_delay
    assert big > small


def test_estimated_delay_is_capped() -> None:
    config = ProcessingConfig()
    huge = config.estimated_delay(UploadType.FILE, 100_000 * _MIB)

    assert huge == config.max_delay
