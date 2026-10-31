import asyncio
from unittest.mock import AsyncMock

import pytest

from maxo import Bot
from maxo.errors import MaxBotBadRequestError
from maxo.utils.upload_media import BufferedInputFile


async def test_aenter_closes_client_when_me_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AsyncMock()
    bot = Bot("token", client=client)
    bot._owns_client = True

    async def boom() -> None:
        raise RuntimeError("bad token")

    monkeypatch.setattr(bot, "me", boom)
    with pytest.raises(RuntimeError):
        await bot.__aenter__()

    client.close.assert_awaited_once()


async def test_empty_file_rejected_before_get_upload_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = Bot("token")

    async def fail(**_: object) -> None:
        raise AssertionError("get_upload_url must not be called")

    monkeypatch.setattr(bot, "get_upload_url", fail)
    with pytest.raises(ValueError, match="пустой"):
        await bot.upload(BufferedInputFile.image(b"", "empty.png"))
    await bot.close()


async def test_build_attachments_cancels_rest_and_raises_plain_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bot = Bot("token", client=AsyncMock())
    slow_cancelled = asyncio.Event()

    async def upload(file: BufferedInputFile, size: int | None = None) -> None:
        if file.file_name == "bad.png":
            raise MaxBotBadRequestError(code="", error="x", message="bad")
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            slow_cancelled.set()
            raise

    monkeypatch.setattr(bot, "upload", upload)
    files = [
        BufferedInputFile.image(b"1", "slow.png"),
        BufferedInputFile.image(b"1", "bad.png"),
    ]

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        await bot.build_attachments([], files=files)

    assert slow_cancelled.is_set()
    assert isinstance(exc_info.value.__cause__, ExceptionGroup)
