from collections.abc import Callable
from contextlib import aclosing
from enum import StrEnum
from typing import Any, Never
from urllib.parse import quote

from aiohttp import ClientError, ClientSession
from aiohttp.hdrs import CONTENT_DISPOSITION, CONTENT_RANGE, CONTENT_TYPE
from unihttp.serialize import ResponseLoader

from maxo.backoff import Backoff, BackoffConfig
from maxo.enums import UploadType
from maxo.errors import MaxBotApiError
from maxo.errors.api import raise_api_error
from maxo.errors.network import to_network_error
from maxo.types.base import MaxoType
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_MIB = 1024 * 1024
_OCTET_STREAM = "application/octet-stream"
_CLIENT_ERROR_STATUS = 400
_SERVER_ERROR_STATUS = 500

_INSTANT_UPLOAD_TYPES = frozenset({UploadType.IMAGE, UploadType.VIDEO})

DEFAULT_NOT_READY_BACKOFF = BackoffConfig(
    min_delay=0.2,
    max_delay=3.0,
    factor=1.6,
    jitter=0.1,
)
DEFAULT_CHUNK_BACKOFF = BackoffConfig(
    min_delay=0.5,
    max_delay=5.0,
    factor=2.0,
    jitter=0.1,
)


class UploadMethod(StrEnum):
    """Способ загрузки медиа на сервер MAX."""

    AUTO = "auto"
    SINGLE = "single"
    RESUMABLE = "resumable"


class UploadConfig(MaxoType):
    """Настройки загрузки медиа для `Bot(upload_config=...)`."""

    method: UploadMethod = UploadMethod.AUTO
    resumable_threshold: int = 50 * _MIB

    chunk_size: int = 50 * _MIB
    chunk_retries: int = 3
    chunk_backoff: BackoffConfig = DEFAULT_CHUNK_BACKOFF

    not_ready_backoff: BackoffConfig = DEFAULT_NOT_READY_BACKOFF
    not_ready_max_retries: int = 10

    processing_base_delay: float = 0.5
    processing_delay_per_mib: float = 0.008
    processing_max_delay: float = 30.0

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("`chunk_size` should be greater than 0")
        if self.chunk_retries < 0:
            raise ValueError("`chunk_retries` should not be negative")
        if self.not_ready_max_retries < 0:
            raise ValueError("`not_ready_max_retries` should not be negative")
        if self.resumable_threshold < 0:
            raise ValueError("`resumable_threshold` should not be negative")
        if self.processing_base_delay < 0:
            raise ValueError("`processing_base_delay` should not be negative")
        if self.processing_delay_per_mib < 0:
            raise ValueError("`processing_delay_per_mib` should not be negative")
        if self.processing_max_delay < 0:
            raise ValueError("`processing_max_delay` should not be negative")

    def should_use_resumable(self, size: int) -> bool:
        if self.method is UploadMethod.RESUMABLE:
            return True
        if self.method is UploadMethod.SINGLE:
            return False
        return size >= self.resumable_threshold

    def estimated_processing_delay(self, upload_type: UploadType, size: int) -> float:
        if upload_type in _INSTANT_UPLOAD_TYPES:
            return 0.0
        delay = self.processing_base_delay + self.processing_delay_per_mib * (
            size / _MIB
        )
        return min(delay, self.processing_max_delay)


async def resumable_upload(
    *,
    url: str,
    file: InputFile,
    session: ClientSession,
    response_loader: ResponseLoader,
    json_loads: Callable[[bytes], Any],
    config: UploadConfig | None = None,
    size: int | None = None,
) -> UploadMediaResult | None:
    """
    Загружает файл частями через выделенную keep-alive сессию.

    `size` - заранее известный размер файла в байтах
    """
    if config is None:
        config = UploadConfig()

    if size is None:
        size = await file.size()
    if size <= 0:
        msg = "Нельзя загрузить пустой файл"
        raise ValueError(msg)

    encoded_name = quote(file.file_name, safe="")
    disposition = f'attachment; filename="{encoded_name}"'

    offset = 0
    final_body = b""
    # aclosing: при ошибке `async for` не закрывает генератор, а у
    # `FSInputFile.stream` внутри него остаётся открытый файл.
    async with aclosing(file.stream(config.chunk_size)) as chunks:
        async for chunk in chunks:
            end = offset + len(chunk) - 1
            headers: dict[str, str] = {
                CONTENT_TYPE: _OCTET_STREAM,
                CONTENT_DISPOSITION: disposition,
                CONTENT_RANGE: f"bytes {offset}-{end}/{size}",
            }
            final_body = await _send_chunk(
                session=session,
                url=url,
                chunk=chunk,
                headers=headers,
                config=config,
                json_loads=json_loads,
            )
            offset += len(chunk)

    if offset != size:
        # Файл изменился между замером размера и чтением
        msg = f"Размер файла изменился во время загрузки: {size} -> {offset} байт"
        raise ValueError(msg)

    return _parse_result(final_body, response_loader, json_loads)


async def _send_chunk(
    *,
    session: ClientSession,
    url: str,
    chunk: bytes,
    headers: dict[str, str],
    config: UploadConfig,
    json_loads: Callable[[bytes], Any],
) -> bytes:
    backoff = Backoff(config.chunk_backoff)
    while True:
        try:
            async with session.post(url, data=chunk, headers=headers) as response:
                body = await response.read()
                if response.status < _CLIENT_ERROR_STATUS:
                    return body
                # 4xx считаем неретраибельными, ретраим только 5xx.
                if (
                    response.status < _SERVER_ERROR_STATUS
                    or backoff.counter >= config.chunk_retries
                ):
                    _raise_upload_error(response.status, body, json_loads)
        # aiohttp кидает голый TimeoutError, он не наследник ClientError.
        except (ClientError, TimeoutError) as error:
            if backoff.counter >= config.chunk_retries:
                raise to_network_error(error) from error

        backoff.next()
        await backoff.sleep()


def _raise_upload_error(
    status: int,
    body: bytes,
    json_loads: Callable[[bytes], Any],
) -> Never:
    raw_data: object = body
    try:
        data = json_loads(body)
    except (ValueError, TypeError):
        message = body.decode("utf-8", "replace")
    else:
        raw_data = data
        if isinstance(data, dict):
            raise_api_error(status, data)
        message = str(data)
    raise MaxBotApiError(
        code="",
        error=f"upload failed with status {status}",
        message=message,
        raw_data=raw_data,
    )


def _parse_result(
    body: bytes,
    response_loader: ResponseLoader,
    json_loads: Callable[[bytes], Any],
) -> UploadMediaResult | None:
    try:
        data = json_loads(body)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    return response_loader.load(data, UploadMediaResult)
