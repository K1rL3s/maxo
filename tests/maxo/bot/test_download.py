from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from unihttp.exceptions import NetworkError

from maxo.bot.bot import Bot
from maxo.bot.middlewares import AuthMiddleware
from maxo.errors import MaxBotNetworkError
from maxo.types import AttachmentPayload


@asynccontextmanager
async def _stream(
    chunks: tuple[bytes, ...],
    closed: list[bool],
) -> AsyncIterator[AsyncIterator[bytes]]:
    async def iterator() -> AsyncIterator[bytes]:
        for chunk in chunks:
            yield chunk

    try:
        yield iterator()
    finally:
        closed.append(True)


def _patch_stream(
    bot: Bot,
    *chunks: bytes,
    closed: list[bool] | None = None,
) -> Any:
    """Подменяет клиент бота; в `closed` попадает факт закрытия потока."""
    response = SimpleNamespace(
        data=_stream(chunks, closed if closed is not None else []),
    )
    call = AsyncMock(return_value=response)
    return patch.object(
        bot.media,
        "_client",
        SimpleNamespace(call_method_stream=call),
    )


async def test_download_returns_whole_payload(bot: Bot) -> None:
    with _patch_stream(bot, b"pay", b"load"):
        result = await bot.media.download("https://example.test/file.bin")

    assert result == b"payload"


async def test_download_to_path_writes_file(bot: Bot, tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"

    with _patch_stream(bot, b"pay", b"load"):
        await bot.media.download_to("https://example.test/file.bin", path)

    assert path.read_bytes() == b"payload"


async def test_download_to_keeps_old_file_on_broken_stream(
    bot: Bot,
    tmp_path: Path,
) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"old")

    @asynccontextmanager
    async def broken() -> AsyncIterator[AsyncIterator[bytes]]:
        async def iterator() -> AsyncIterator[bytes]:
            yield b"pay"
            raise NetworkError("connection reset")

        yield iterator()

    response = SimpleNamespace(data=broken())
    client = SimpleNamespace(call_method_stream=AsyncMock(return_value=response))
    with (
        patch.object(bot.media, "_client", client),
        pytest.raises(MaxBotNetworkError),
    ):
        await bot.media.download_to("https://example.test/file.bin", path)

    assert path.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [path]


async def test_download_to_does_not_touch_foreign_part_file(
    bot: Bot,
    tmp_path: Path,
) -> None:
    path = tmp_path / "payload.bin"
    foreign = tmp_path / "payload.bin.part"
    foreign.write_bytes(b"foreign")

    with _patch_stream(bot, b"pay", b"load"):
        await bot.media.download_to("https://example.test/file.bin", path)

    assert path.read_bytes() == b"payload"
    assert foreign.read_bytes() == b"foreign"


async def test_download_stream_yields_chunks_as_they_come(bot: Bot) -> None:
    """Стрим не склеивает чанки: на этом держится и прогресс, и запись
    в чужой буфер без буферизации файла целиком в память."""
    with _patch_stream(bot, b"pay", b"load"):
        async with bot.media.download_stream("https://e.test/f.bin") as stream:
            chunks = [chunk async for chunk in stream]

    assert chunks == [b"pay", b"load"]


async def test_download_unwraps_attachment_payload(bot: Bot) -> None:
    payload = AttachmentPayload(url="https://example.test/file.bin")

    with _patch_stream(bot, b"payload") as client:
        await bot.media.download(payload)

    call = client.call_method_stream
    assert call.await_args.args[0].url == "https://example.test/file.bin"


async def test_download_uses_media_middleware(bot: Bot) -> None:
    """An attachment URL may lead to another host, so no token goes there:
    downloads use the `Media` client and its chain without `AuthMiddleware`."""
    with _patch_stream(bot, b"payload") as client:
        await bot.media.download("https://example.test/file.bin")

    used = client.call_method_stream.await_args.kwargs["middleware"]
    assert used == bot.media.middleware
    assert not any(isinstance(m, AuthMiddleware) for m in used)


async def test_download_stream_closes_response_on_break(bot: Bot) -> None:
    """Соединение освобождается на `break` без участия вызывающего - ради
    этого `download_stream` и сделан контекстным менеджером."""
    closed: list[bool] = []

    with _patch_stream(bot, b"pay", b"load", closed=closed):
        async with bot.media.download_stream("https://e.test/f.bin") as chunks:
            async for _ in chunks:
                break

    assert closed == [True]


async def test_download_stream_keeps_caller_errors_as_is(bot: Bot) -> None:
    """Errors from the caller's `async with` body are not wrapped into maxo ones."""
    with (
        _patch_stream(bot, b"payload"),
        pytest.raises(TimeoutError),
    ):
        async with bot.media.download_stream("https://e.test/f.bin"):
            raise TimeoutError


async def test_download_wraps_network_error_raised_mid_body(bot: Bot) -> None:
    @asynccontextmanager
    async def body_breaking_after_first_chunk() -> AsyncIterator[AsyncIterator[bytes]]:
        async def chunks() -> AsyncIterator[bytes]:
            yield b"pay"
            raise NetworkError("connection reset")

        yield chunks()

    call_method_stream = AsyncMock(
        return_value=SimpleNamespace(data=body_breaking_after_first_chunk()),
    )
    with (
        patch.object(
            bot.media,
            "_client",
            SimpleNamespace(call_method_stream=call_method_stream),
        ),
        pytest.raises(MaxBotNetworkError) as exc_info,
    ):
        await bot.media.download("https://example.test/file.bin")

    assert isinstance(exc_info.value.__cause__, NetworkError)
