import json
from collections.abc import AsyncGenerator, Iterable
from typing import Any
from unittest.mock import AsyncMock, patch
from urllib.parse import unquote

import pytest
from aiohttp import ClientConnectionError

from maxo.bot.upload import UploadConfig, UploadMethod, resumable_upload
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
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import BufferedInputFile, InputFile

_MIB = 1024 * 1024


class _FakeResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    async def read(self) -> bytes:
        return self._body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None


class _FakeSession:
    def __init__(self, responses: Iterable[_FakeResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        data: bytes,
        headers: dict[str, str],
    ) -> _FakeResponse:
        self.calls.append({"url": url, "data": data, "headers": headers})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class _Retort:
    def load(self, data: Any, tp: type) -> Any:
        return tp(**data)


async def _run(
    session: _FakeSession,
    data: bytes,
    chunk_size: int,
    chunk_retries: int = 3,
) -> UploadMediaResult | None:
    file = BufferedInputFile.file(data, "f.bin")
    return await resumable_upload(
        url="https://upload.example/upload.do",
        file=file,
        session=session,  # type: ignore[arg-type]
        response_loader=_Retort(),
        json_loads=json.loads,
        config=UploadConfig(chunk_size=chunk_size, chunk_retries=chunk_retries),
    )


async def test_sends_chunks_with_correct_content_range() -> None:
    session = _FakeSession(
        [
            _FakeResponse(201, b"0-3/10"),
            _FakeResponse(201, b"0-7/10"),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    result = await _run(session, b"abcdefghij", 4)

    assert isinstance(result, UploadMediaResult)
    assert result.token == "tok"  # noqa: S105
    ranges = [call["headers"]["Content-Range"] for call in session.calls]
    assert ranges == ["bytes 0-3/10", "bytes 4-7/10", "bytes 8-9/10"]
    assert [call["data"] for call in session.calls] == [b"abcd", b"efgh", b"ij"]
    assert 'filename="f.bin"' in session.calls[0]["headers"]["Content-Disposition"]


async def test_single_chunk_small_file() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])

    result = await _run(session, b"hello", 1024)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert session.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


async def test_non_json_final_body_returns_none() -> None:
    session = _FakeSession([_FakeResponse(200, b"0-4/5")])

    assert await _run(session, b"hello", 1024) is None


async def test_json_non_dict_final_body_returns_none() -> None:
    session = _FakeSession([_FakeResponse(200, b'["0-4/5"]')])

    assert await _run(session, b"hello", 1024) is None


async def test_empty_file_raises() -> None:
    session = _FakeSession([])

    with pytest.raises(ValueError, match="пустой файл"):
        await _run(session, b"", 1024)


async def test_content_disposition_is_latin1_safe() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])
    file_name = 'файл "1".bin'
    file = BufferedInputFile.file(b"hello", file_name)

    await resumable_upload(
        url="https://upload.example/upload.do",
        file=file,
        session=session,  # type: ignore[arg-type]
        response_loader=_Retort(),
        json_loads=json.loads,
    )

    disposition = session.calls[0]["headers"]["Content-Disposition"]
    disposition.encode("latin-1")
    encoded = disposition.removeprefix('attachment; filename="').removesuffix('"')
    assert unquote(encoded) == file_name


async def test_explicit_total_skips_size_call() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])
    file = BufferedInputFile.file(b"hello", "f.bin")

    with patch.object(
        BufferedInputFile,
        "size",
        side_effect=AssertionError("size() не должен вызываться"),
    ):
        result = await resumable_upload(
            url="https://upload.example/upload.do",
            file=file,
            session=session,  # type: ignore[arg-type]
            response_loader=_Retort(),
            json_loads=json.loads,
            size=5,
        )

    assert result is not None
    assert session.calls[0]["headers"]["Content-Range"] == "bytes 0-4/5"


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
    session = _FakeSession([_FakeResponse(400, b"nope")])
    file = _TrackingInputFile()

    with pytest.raises(MaxBotApiError):
        await resumable_upload(
            url="https://upload.example/upload.do",
            file=file,
            session=session,  # type: ignore[arg-type]
            response_loader=_Retort(),
            json_loads=json.loads,
            config=UploadConfig(chunk_size=4),
        )

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
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])
    file = BufferedInputFile.file(b"hello", "f.bin")

    result = await resumable_upload(
        url="https://upload.example/upload.do",
        file=file,
        session=session,  # type: ignore[arg-type]
        response_loader=_Retort(),
        json_loads=json.loads,
    )

    assert result is not None
    assert result.token == "tok"  # noqa: S105


async def test_client_error_status_raises_without_retry() -> None:
    session = _FakeSession([_FakeResponse(406, b'{"code": "upload.error"}')])

    with pytest.raises(MaxBotApiError):
        await _run(session, b"hello", 1024)

    assert len(session.calls) == 1


async def test_non_json_error_status_raises_base_error() -> None:
    session = _FakeSession([_FakeResponse(406, b"plain error")])

    with pytest.raises(MaxBotApiError) as exc_info:
        await _run(session, b"hello", 1024)

    error = exc_info.value
    assert error.error == "upload failed with status 406"
    assert error.message == "plain error"
    assert error.raw_data == b"plain error"


async def test_json_non_dict_error_status_raises_base_error() -> None:
    session = _FakeSession([_FakeResponse(406, b'["plain error"]')])

    with pytest.raises(MaxBotApiError) as exc_info:
        await _run(session, b"hello", 1024)

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
    session = _FakeSession([_FakeResponse(status, json.dumps(payload).encode())])

    with pytest.raises(error_class) as exc_info:
        await _run(session, b"hello", 1024)

    error = exc_info.value
    assert error.code == "proto.payload"
    assert error.error == "attachment.not.ready"
    assert error.message == "cannot process attachment"
    assert error.raw_data == payload
    assert len(session.calls) == 1


async def test_server_error_is_retried_then_succeeds() -> None:
    session = _FakeSession(
        [
            _FakeResponse(500, b'{"message": "temporary"}'),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await _run(session, b"hello", 1024, chunk_retries=3)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert len(session.calls) == 2


async def test_network_error_is_retried_then_reraised() -> None:
    session = _FakeSession(
        [
            ClientConnectionError("boom"),
            ClientConnectionError("boom"),
        ],
    )

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(MaxBotNetworkError, match="boom") as exc_info,
    ):
        await _run(session, b"hello", 1024, chunk_retries=1)

    assert len(session.calls) == 2
    # Исходная ошибка aiohttp не теряется.
    assert isinstance(exc_info.value.__cause__, ClientConnectionError)


async def test_timeout_is_retried_then_succeeds() -> None:
    # aiohttp кидает голый TimeoutError, он не наследник ClientError.
    session = _FakeSession(
        [
            TimeoutError("timed out"),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    with patch("asyncio.sleep", new_callable=AsyncMock):
        result = await _run(session, b"hello", 1024, chunk_retries=3)

    assert result is not None
    assert result.token == "tok"  # noqa: S105
    assert len(session.calls) == 2


async def test_timeout_is_reraised_after_retries() -> None:
    session = _FakeSession([TimeoutError("timed out"), TimeoutError("timed out")])

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(MaxBotTimeoutError, match="timed out") as exc_info,
    ):
        await _run(session, b"hello", 1024, chunk_retries=1)

    assert len(session.calls) == 2
    assert isinstance(exc_info.value.__cause__, TimeoutError)


async def test_network_error_is_a_maxo_error() -> None:
    # Ловить сетевые сбои можно одним `except MaxoError`.
    assert issubclass(MaxBotNetworkError, MaxoError)
    assert issubclass(MaxBotTimeoutError, MaxBotNetworkError)


async def test_empty_aiohttp_error_message_falls_back_to_class_name() -> None:
    session = _FakeSession([ClientConnectionError()])

    with pytest.raises(MaxBotNetworkError, match="ClientConnectionError"):
        await _run(session, b"hello", 1024, chunk_retries=0)


async def test_first_retry_waits_backoff_min_delay() -> None:
    session = _FakeSession(
        [
            _FakeResponse(500, b"temporary"),
            _FakeResponse(200, b'{"token": "tok"}'),
        ],
    )

    with patch("asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
        await _run(session, b"hello", 1024, chunk_retries=3)

    # Первая пауза - ровно `min_delay`, а не удвоенная.
    first_delay = sleep_mock.await_args_list[0].args[0]
    assert first_delay == UploadConfig().chunk_backoff.min_delay


async def test_size_mismatch_raises() -> None:
    session = _FakeSession([_FakeResponse(200, b'{"token": "tok"}')])
    file = BufferedInputFile.file(b"hello", "f.bin")

    # Файл «усох» между замером размера и стримом.
    with pytest.raises(ValueError, match="изменился во время загрузки"):
        await resumable_upload(
            url="https://upload.example/upload.do",
            file=file,
            session=session,  # type: ignore[arg-type]
            response_loader=_Retort(),
            json_loads=json.loads,
            size=999,
        )


async def test_server_error_is_raised_after_retries() -> None:
    session = _FakeSession(
        [
            _FakeResponse(500, b"temporary"),
            _FakeResponse(500, b"temporary"),
        ],
    )

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        pytest.raises(MaxBotApiError) as exc_info,
    ):
        await _run(session, b"hello", 1024, chunk_retries=1)

    assert exc_info.value.error == "upload failed with status 500"
    assert len(session.calls) == 2


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
