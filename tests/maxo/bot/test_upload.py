from collections.abc import AsyncGenerator, Iterable
from functools import partial
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

import pytest
from unihttp.exceptions import NetworkError as UnihttpNetworkError

from maxo.backoff import BackoffConfig
from maxo.bot.methods.upload.chunk_upload import UploadResponseBody
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.enums import UploadType
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotNetworkError,
    MaxBotTimeoutError,
    MaxBotTooManyRequestsError,
    MaxBotUnsupportedMediaTypeError,
    MaxoError,
)
from maxo.errors.network import to_network_error
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile, InputFile
from tests.factories import make_bot

_MIB = 1024 * 1024


def _network_error(cause: Exception) -> MaxBotNetworkError:
    """Имитирует `raise to_network_error(error) from error` из `make_request`."""
    error = to_network_error(cause)
    error.__cause__ = cause
    return error


class _FakeResponse:
    """`data` - как его уже отдал бы `AiohttpAsyncClient.make_request`: JSON
    распарсен в dict/list, а нераспарсиваемое тело осталось raw-байтами."""

    def __init__(self, status_code: int, data: UploadResponseBody) -> None:
        self.status_code = status_code
        self.data = data


class _FakeClient:
    """HTTP-клиент бота: отдаёт заготовленные ответы и пишет запросы.
    Per-call `middleware=[ChunkUploadRetryMiddleware(...)]` тут просто
    игнорируется, ретраи по нему проверяются отдельно в
    `test_chunk_upload_retry_middleware.py`."""

    def __init__(self, responses: Iterable[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def call_method(
        self,
        method: Any,
        *,
        middleware: Any = None,
    ) -> _FakeResponse:
        self.calls.append(
            {"url": method.url, "data": method.chunk, "headers": method.headers},
        )
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


_URL = "https://upload.example/upload.do"


async def test_sends_chunks_with_correct_content_range() -> None:
    client = _FakeClient(
        [
            _FakeResponse(201, b"0-3/10"),
            _FakeResponse(201, b"0-7/10"),
            _FakeResponse(200, {"token": "tok"}),
        ],
    )

    bot = make_bot(client=client, upload_config=UploadConfig(chunk_size=4))
    result = await bot.upload_media_resumable(
        _URL,
        BufferedInputFile.file(b"abcdefghij", "f.bin"),
    )

    assert isinstance(result, UploadMediaResult)
    assert result.token == "tok"  # noqa: S105
    ranges = [call["headers"]["Content-Range"] for call in client.calls]
    assert ranges == ["bytes 0-3/10", "bytes 4-7/10", "bytes 8-9/10"]
    assert [call["data"] for call in client.calls] == [b"abcd", b"efgh", b"ij"]
    assert 'filename="f.bin"' in client.calls[0]["headers"]["Content-Disposition"]


async def test_single_chunk_small_file() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])

    bot = make_bot(client=client)
    result = await bot.upload_media_resumable(
        _URL,
        BufferedInputFile.file(b"hello", "f.bin"),
    )

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert client.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


async def test_non_json_final_body_returns_none() -> None:
    client = _FakeClient([_FakeResponse(200, b"0-4/5")])

    bot = make_bot(client=client)
    assert (
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )
        is None
    )


async def test_json_non_dict_final_body_returns_none() -> None:
    client = _FakeClient([_FakeResponse(200, ["0-4/5"])])

    bot = make_bot(client=client)
    assert (
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )
        is None
    )


async def test_empty_file_raises() -> None:
    client = _FakeClient([])

    bot = make_bot(client=client)

    with pytest.raises(ValueError, match="пустой файл"):
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"", "f.bin"),
        )


async def test_content_disposition_is_latin1_safe() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])
    file_name = 'файл "1".bin'
    file = BufferedInputFile.file(b"hello", file_name)

    await make_bot(client=client).upload_media_resumable(_URL, file)

    disposition = client.calls[0]["headers"]["Content-Disposition"]
    disposition.encode("latin-1")
    encoded = disposition.removeprefix('attachment; filename="').removesuffix('"')
    assert unquote(encoded) == file_name


async def test_explicit_total_skips_size_call() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])
    file = BufferedInputFile.file(b"hello", "f.bin")
    bot = make_bot(client=client)

    with patch.object(
        BufferedInputFile,
        "size",
        side_effect=AssertionError("size() не должен вызываться"),
    ):
        result = await bot.upload_media_resumable(_URL, file, size=5)

    assert result is not None
    assert client.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


class _TrackingInputFile(InputFile):
    """Считает, закрыли ли `stream()` - у `FSInputFile` там открытый файл."""

    def __init__(self) -> None:
        self.closed = False

    @property
    def file_name(self) -> str:
        return "f.bin"

    @property
    def type(self) -> UploadType:
        return UploadType.FILE

    async def read(self) -> bytes:
        return b"abcdefghij"

    async def stream(self, chunk_size: int) -> AsyncGenerator[bytes, None]:
        data = await self.read()
        try:
            for start in range(0, len(data), chunk_size):
                yield data[start : start + chunk_size]
        finally:
            self.closed = True


async def test_stream_is_closed_when_chunk_fails() -> None:
    client = _FakeClient([_FakeResponse(400, b"nope")])
    file = _TrackingInputFile()
    bot = make_bot(client=client, upload_config=UploadConfig(chunk_size=4))

    with pytest.raises(MaxBotApiError):
        await bot.upload_media_resumable(_URL, file)

    assert file.closed is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"chunk_size": 0},
        {"chunk_retries": -1},
        {"not_ready_max_retries": -1},
        {"resumable_threshold": -1},
        {"processing_base_delay": -1},
        {"processing_delay_per_mib": -1},
        {"processing_max_delay": -1},
    ],
)
def test_upload_config_rejects_invalid_values(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="should"):
        UploadConfig(**kwargs)  # type: ignore[arg-type]


async def test_default_config_is_used() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])
    file = BufferedInputFile.file(b"hello", "f.bin")

    result = await make_bot(client=client).upload_media_resumable(_URL, file)

    assert result is not None
    assert result.token == "tok"  # noqa: S105


async def test_client_error_status_raises_without_retry() -> None:
    client = _FakeClient([_FakeResponse(406, {"code": "upload.error"})])

    bot = make_bot(client=client)

    with pytest.raises(MaxBotApiError):
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    assert len(client.calls) == 1


async def test_non_json_error_status_raises_base_error() -> None:
    client = _FakeClient([_FakeResponse(406, b"plain error")])

    bot = make_bot(client=client)

    with pytest.raises(MaxBotApiError) as exc_info:
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    error = exc_info.value
    assert error.error == "upload failed with status 406"
    assert error.message == "plain error"
    assert error.raw_data == b"plain error"


async def test_json_non_dict_error_status_raises_base_error() -> None:
    client = _FakeClient([_FakeResponse(406, ["plain error"])])

    bot = make_bot(client=client)

    with pytest.raises(MaxBotApiError) as exc_info:
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    error = exc_info.value
    assert error.error == "upload failed with status 406"
    assert error.message == "['plain error']"
    assert error.raw_data == ["plain error"]


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

    bot = make_bot(client=client)

    with pytest.raises(error_class) as exc_info:
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    error = exc_info.value
    assert error.code == "proto.payload"
    assert error.error == "attachment.not.ready"
    assert error.message == "cannot process attachment"
    assert error.raw_data == payload
    assert len(client.calls) == 1


async def test_server_error_status_raises_immediately() -> None:
    # Ретраи 5xx теперь целиком в `ChunkUploadRetryMiddleware`
    # (`tests/maxo/bot/test_chunk_upload_retry_middleware.py`) - тут только
    # проверяем, что `Bot.upload_media_resumable` сам не ретраит и не глотает ошибку.
    client = _FakeClient([_FakeResponse(500, b"temporary")])

    bot = make_bot(client=client)

    with pytest.raises(MaxBotApiError) as exc_info:
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    assert exc_info.value.error == "upload failed with status 500"
    assert len(client.calls) == 1


async def test_network_error_propagates_without_retry() -> None:
    # См. комментарий выше - ретраи сети живут в `ChunkUploadRetryMiddleware`.
    client = _FakeClient([_network_error(ConnectionError("boom"))])

    bot = make_bot(client=client)

    with pytest.raises(MaxBotNetworkError, match="boom") as exc_info:
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    assert len(client.calls) == 1
    assert isinstance(exc_info.value.__cause__, ConnectionError)


class _ChainRunningClient:
    """Реально прогоняет цепочку middleware (в отличие от `_ChainRunningClient`)
    и всегда падает сетевой ошибкой транспорта."""

    def __init__(self) -> None:
        self.attempts = 0

    async def call_method(
        self,
        method: Any,
        *,
        middleware: Any = None,
    ) -> _FakeResponse:
        async def terminal(request: Any) -> _FakeResponse:
            self.attempts += 1
            raise UnihttpNetworkError("boom")

        handler = terminal
        for m in reversed(list(middleware or ())):
            handler = partial(m.handle, next_handler=handler)
        return await handler(MagicMock())


async def test_chunk_retries_apply_to_raw_transport_errors() -> None:
    client = _ChainRunningClient()
    bot = make_bot(
        client=client,
        upload_config=UploadConfig(
            chunk_retries=2,
            chunk_backoff=BackoffConfig(
                min_delay=0.0,
                max_delay=0.001,
                factor=2.0,
                jitter=0.0,
            ),
        ),
    )

    with pytest.raises(MaxBotNetworkError):
        await bot.upload_media_resumable(
            _URL,
            BufferedInputFile.file(b"hello", "f.bin"),
        )

    assert client.attempts == 3


async def test_network_error_is_a_maxo_error() -> None:
    # Ловить сетевые сбои можно одним `except MaxoError`.
    assert issubclass(MaxBotNetworkError, MaxoError)
    assert issubclass(MaxBotTimeoutError, MaxBotNetworkError)


async def test_size_mismatch_raises() -> None:
    client = _FakeClient([_FakeResponse(200, {"token": "tok"})])
    file = BufferedInputFile.file(b"hello", "f.bin")
    bot = make_bot(client=client)

    # Файл «усох» между замером размера и стримом.
    with pytest.raises(ValueError, match="изменился во время загрузки"):
        await bot.upload_media_resumable(_URL, file, size=999)


def test_should_use_resumable_respects_explicit_method() -> None:
    assert UploadConfig(method=UploadMethod.RESUMABLE).should_use_resumable(1) is True
    assert UploadConfig(method=UploadMethod.SINGLE).should_use_resumable(10**9) is False


def test_should_use_resumable_auto_by_threshold() -> None:
    config = UploadConfig(method=UploadMethod.AUTO, resumable_threshold=100)
    assert config.should_use_resumable(99) is False
    assert config.should_use_resumable(100) is True


def test_default_everyday_files_stay_single() -> None:
    # Обычные загрузки (фото, документы, короткие видео) должны идти тем же
    # single-путём, что и до появления resumable, - без заметной разницы
    config = UploadConfig()
    assert config.should_use_resumable(1 * _MIB) is False
    assert config.should_use_resumable(config.resumable_threshold - 1) is False


def test_default_chunk_equals_threshold_so_boundary_is_one_request() -> None:
    # Инвариант: файл ровно на пороге уходит одним куском (одним запросом),
    # как прежний single-аплоад - переход в resumable незаметен
    config = UploadConfig()
    assert config.chunk_size == config.resumable_threshold
    assert config.should_use_resumable(config.resumable_threshold) is True
    chunks = -(-config.resumable_threshold // config.chunk_size)
    assert chunks == 1


@pytest.mark.parametrize("upload_type", [UploadType.IMAGE, UploadType.VIDEO])
def test_estimated_delay_zero_for_instant_types(upload_type: UploadType) -> None:
    assert UploadConfig().estimated_processing_delay(upload_type, 100 * _MIB) == 0.0


@pytest.mark.parametrize("upload_type", [UploadType.FILE, UploadType.AUDIO])
def test_estimated_delay_grows_with_size(upload_type: UploadType) -> None:
    config = UploadConfig()
    small = config.estimated_processing_delay(upload_type, 1 * _MIB)
    big = config.estimated_processing_delay(upload_type, 100 * _MIB)

    assert small >= config.processing_base_delay
    assert big > small


def test_estimated_delay_is_capped() -> None:
    config = UploadConfig()
    huge = config.estimated_processing_delay(UploadType.FILE, 100_000 * _MIB)

    assert huge == config.processing_max_delay
