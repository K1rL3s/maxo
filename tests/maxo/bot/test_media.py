from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, call, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.media import Media
from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.bot.upload import ProcessingConfig, UploadConfig, UploadMethod
from maxo.enums import UploadType
from maxo.errors.api import MaxBotResponseError
from maxo.types import (
    AudioAttachmentRequest,
    CallbackButton,
    FileAttachmentRequest,
    InlineKeyboardAttachmentRequest,
    PhotoAttachmentRequest,
    UploadEndpoint,
    UploadMediaResult,
    VideoAttachmentRequest,
)
from maxo.types.media_input import MediaInput
from maxo.utils.upload_media import BufferedInputFile, FSInputFile

if TYPE_CHECKING:
    from unihttp.http import UploadFile


@pytest.fixture
def media_call() -> Iterator[AsyncMock]:
    """Requests to the file hosts: `Media.call_method`."""
    with patch.object(Media, "call_method", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def upload(bot: Bot) -> Iterator[AsyncMock]:
    with patch.object(bot, "upload", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def sleep() -> Iterator[AsyncMock]:
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock:
        yield mock


def _set_endpoint(bot: Bot, token: str | None = None) -> None:
    kwargs = {} if token is None else {"token": token}
    bot.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com/upload", **kwargs),
    )


@pytest.fixture
def resumable() -> Iterator[AsyncMock]:
    with patch.object(
        Media,
        "_upload_resumable",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


async def test_build_media_only_input_files(
    bot: Bot,
    upload: AsyncMock,
    sleep: AsyncMock,
) -> None:
    input_files = [
        BufferedInputFile.image(b"photo_bytes", "photo.jpg"),
        BufferedInputFile.video(b"video_bytes", "video.mp4"),
    ]
    uploaded_attachments = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
        VideoAttachmentRequest.factory(token="video_token"),  # noqa: S106
    ]

    upload.side_effect = uploaded_attachments
    result = await bot._build_media(input_files)

    assert upload.await_args_list == [
        call(input_files[0], len(b"photo_bytes")),
        call(input_files[1], len(b"video_bytes")),
    ]
    sleep.assert_not_awaited()

    assert result == uploaded_attachments


async def test_build_media_waits_for_file_type(
    bot: Bot,
    upload: AsyncMock,
    sleep: AsyncMock,
) -> None:
    data = b"x" * (2 * 1024 * 1024)
    input_files = [BufferedInputFile.file(data, "big.bin")]
    uploaded_attachments = [
        FileAttachmentRequest.factory(token="file_token"),  # noqa: S106
    ]

    upload.side_effect = uploaded_attachments
    result = await bot._build_media(input_files)

    expected_delay = ProcessingConfig().estimated_delay(
        UploadType.FILE,
        len(data),
    )
    sleep.assert_awaited_once_with(expected_delay)

    assert result == uploaded_attachments


async def test_build_media_only_requests(
    bot: Bot,
    upload: AsyncMock,
    sleep: AsyncMock,
) -> None:
    requests: list[MediaInput] = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
        VideoAttachmentRequest.factory(token="video_token"),  # noqa: S106
    ]

    result = await bot._build_media(requests)

    upload.assert_not_called()
    sleep.assert_not_awaited()

    assert result == requests


async def test_build_media_mixed_order(
    bot: Bot,
    upload: AsyncMock,
    sleep: AsyncMock,
) -> None:
    input_file1 = BufferedInputFile.image(b"photo_bytes", "photo.jpg")
    request1 = VideoAttachmentRequest.factory(token="video_token")  # noqa: S106
    input_file2 = BufferedInputFile.image(b"photo_bytes2", "photo2.jpg")
    request2 = VideoAttachmentRequest.factory(token="video_token2")  # noqa: S106

    files: Sequence[MediaInput] = [input_file1, request1, input_file2, request2]

    uploaded_attachments = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
        PhotoAttachmentRequest.factory(token="photo_token2"),  # noqa: S106
    ]

    expected_result = [
        uploaded_attachments[0],
        request1,
        uploaded_attachments[1],
        request2,
    ]

    upload.side_effect = uploaded_attachments
    result = await bot._build_media(files)

    assert upload.await_args_list == [
        call(input_file1, len(b"photo_bytes")),
        call(input_file2, len(b"photo_bytes2")),
    ]
    sleep.assert_not_awaited()

    assert result == expected_result


async def test_build_attachments_no_files(bot: Bot) -> None:
    with patch.object(
        bot,
        "_build_media",
        new_callable=AsyncMock,
    ) as build_media_mock:
        result = await bot.build_attachments(base=[], files=None, keyboard=None)
        build_media_mock.assert_not_called()

    assert result == []


async def test_build_attachments_with_keyboard(bot: Bot) -> None:
    button = CallbackButton(text="open", payload="payload")

    result = await bot.build_attachments(base=[], keyboard=((button,),), files=None)

    assert len(result) == 1
    attachment = result[0]
    assert isinstance(attachment, InlineKeyboardAttachmentRequest)
    assert attachment.payload.buttons == [[button]]


async def test_build_attachments_with_files(bot: Bot) -> None:
    input_files = [BufferedInputFile.image(b"photo_bytes", "photo.jpg")]
    built_media = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
    ]

    with patch.object(
        bot,
        "_build_media",
        new_callable=AsyncMock,
    ) as build_media_mock:
        build_media_mock.return_value = built_media
        result = await bot.build_attachments(
            base=[],
            files=input_files,
            keyboard=None,
        )
        build_media_mock.assert_called_once_with(input_files)

    assert result == built_media


async def test_upload_media_uses_resumable_when_configured(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
) -> None:
    file = BufferedInputFile.video(b"video", "video.mp4")
    bot.media.config = UploadConfig(method=UploadMethod.RESUMABLE)
    _set_endpoint(bot, "endpoint-token")
    resumable.return_value = UploadMediaResult(token="result-token")  # noqa: S106

    assert await bot.upload(file) == VideoAttachmentRequest.factory("endpoint-token")
    resumable.assert_awaited_once_with(
        "https://example.com/upload",
        file,
        len(b"video"),
    )
    media_call.assert_not_called()


@pytest.mark.parametrize(
    "file",
    [
        BufferedInputFile.image(b"image", "image.png"),
        BufferedInputFile.file(b"file", "f.bin"),
    ],
)
async def test_files_and_images_never_go_in_chunks(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
    file: BufferedInputFile,
) -> None:
    """The file host keeps an upload on one connection only and accepts a single
    multipart request over 2 GiB, so chunking is pointless."""
    bot.media.config = UploadConfig(method=UploadMethod.RESUMABLE)
    _set_endpoint(bot)
    media_call.return_value = UploadMediaResult(token="single-token")  # noqa: S106

    await bot.upload(file)

    resumable.assert_not_called()
    media_call.assert_awaited_once()


async def test_fs_file_is_sent_as_open_file(
    bot: Bot,
    media_call: AsyncMock,
    tmp_path: Path,
) -> None:
    """A file from disk is sent as an open file, not read into memory."""
    path = tmp_path / "big.bin"
    path.write_bytes(b"content")
    seen: list[UploadFile] = []

    async def send(method: UploadMedia, **_: object) -> UploadMediaResult:
        seen.append(method.file)
        assert not isinstance(method.file.file, bytes)
        assert method.file.file.read() == b"content"  # type: ignore[union-attr]  # checked above
        return UploadMediaResult(token="single-token")  # noqa: S106

    bot.media.config = UploadConfig()
    _set_endpoint(bot)
    media_call.side_effect = send

    await bot.upload(FSInputFile.file(path))

    assert seen[0].filename == "big.bin"
    assert seen[0].file.closed  # type: ignore[union-attr]  # an open file object


async def test_upload_media_uses_single_when_configured(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
) -> None:
    file = BufferedInputFile.video(b"video", "video.mp4")
    bot.media.config = UploadConfig(method=UploadMethod.SINGLE)
    _set_endpoint(bot)
    media_call.return_value = UploadMediaResult(token="result-token")  # noqa: S106

    assert await bot.upload(file) == VideoAttachmentRequest.factory("result-token")
    media_call.assert_awaited_once()
    resumable.assert_not_called()


async def test_upload_media_single_retval_falls_back_to_endpoint_token(
    bot: Bot,
    media_call: AsyncMock,
) -> None:
    file = BufferedInputFile.video(b"video", "video.mp4")
    bot.media.config = UploadConfig(method=UploadMethod.SINGLE)
    _set_endpoint(bot, "endpoint-token")
    media_call.return_value = None

    assert await bot.upload(file) == VideoAttachmentRequest.factory("endpoint-token")


async def test_upload_media_auto_small_uses_single(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
) -> None:
    file = BufferedInputFile.file(b"tiny", "f.bin")
    bot.media.config = UploadConfig(method=UploadMethod.AUTO)
    _set_endpoint(bot)
    media_call.return_value = UploadMediaResult(token="single-token")  # noqa: S106

    assert await bot.upload(file) == FileAttachmentRequest.factory("single-token")
    media_call.assert_awaited_once()
    resumable.assert_not_called()


async def test_upload_media_auto_large_uses_resumable(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
) -> None:
    file = BufferedInputFile.audio(b"large-enough", "a.mp3")
    bot.media.config = UploadConfig(
        method=UploadMethod.AUTO,
        resumable_threshold=4,
    )
    _set_endpoint(bot)
    resumable.return_value = UploadMediaResult(token="resumable-token")  # noqa: S106

    assert await bot.upload(file) == AudioAttachmentRequest.factory("resumable-token")

    resumable.assert_awaited_once()
    media_call.assert_not_called()


async def test_upload_media_raises_without_any_token(
    bot: Bot,
    resumable: AsyncMock,
) -> None:
    file = BufferedInputFile.audio(b"audio", "audio.mp3")
    bot.media.config = UploadConfig(method=UploadMethod.RESUMABLE)
    _set_endpoint(bot)
    resumable.return_value = None

    with pytest.raises(MaxBotResponseError, match="токен"):
        await bot.upload(file)


@pytest.mark.parametrize(
    "method",
    [UploadMethod.SINGLE, UploadMethod.AUTO, UploadMethod.RESUMABLE],
)
async def test_upload_media_empty_file_rejected(
    bot: Bot,
    media_call: AsyncMock,
    resumable: AsyncMock,
    method: UploadMethod,
) -> None:
    file = BufferedInputFile.file(b"", "empty.bin")
    bot.media.config = UploadConfig(method=method)
    _set_endpoint(bot)

    with pytest.raises(ValueError, match="пустой файл"):
        await bot.upload(file)

    media_call.assert_not_called()
    resumable.assert_not_called()
