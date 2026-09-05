from collections.abc import Sequence
from typing import cast
from unittest.mock import AsyncMock, patch

import pytest

from maxo.bot.bot import Bot
from maxo.bot.upload import UploadConfig, UploadMethod
from maxo.enums import UploadType
from maxo.errors.api import RetvalReturnedServerException
from maxo.types import (
    AudioAttachmentRequest,
    CallbackButton,
    FileAttachmentRequest,
    InlineKeyboardAttachmentRequest,
    Message,
    PhotoAttachmentRequest,
    UploadEndpoint,
    UploadMediaResult,
    VideoAttachmentRequest,
)
from maxo.types.facades.attachments import AttachmentsFacade, MediaInput
from maxo.types.facades.message import MessageMethodsFacade
from maxo.utils.upload_media import BufferedInputFile


class DummyFacade(AttachmentsFacade):
    pass


class DummyMessageFacade(MessageMethodsFacade):
    @property
    def message(self) -> Message:
        return AsyncMock()

    @property
    def chat_id(self) -> int:
        return 0


@pytest.fixture
def bot_mock() -> AsyncMock:
    bot = AsyncMock(spec=Bot)
    bot.upload_config = UploadConfig()
    return bot


@pytest.fixture
def facade(bot_mock: AsyncMock) -> DummyFacade:
    return DummyFacade(bot=bot_mock)


@pytest.fixture
def message_facade(bot_mock: AsyncMock) -> DummyMessageFacade:
    return DummyMessageFacade(bot=bot_mock)


async def test_build_media_only_input_files(facade: DummyFacade) -> None:
    input_files = [
        BufferedInputFile.image(b"photo_bytes", "photo.jpg"),
        BufferedInputFile.video(b"video_bytes", "video.mp4"),
    ]
    uploaded_attachments = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
        VideoAttachmentRequest.factory(token="video_token"),  # noqa: S106
    ]

    with (
        patch.object(
            facade,
            "build_media_attachments",
            new_callable=AsyncMock,
        ) as build_media_attachments_mock,
        patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        build_media_attachments_mock.return_value = uploaded_attachments
        result = await facade._build_media(input_files)

        build_media_attachments_mock.assert_called_once_with(
            input_files,
            [len(b"photo_bytes"), len(b"video_bytes")],
        )
        sleep_mock.assert_not_awaited()

    assert result == uploaded_attachments


async def test_build_media_waits_for_file_type(facade: DummyFacade) -> None:
    data = b"x" * (2 * 1024 * 1024)
    input_files = [BufferedInputFile.file(data, "big.bin")]
    uploaded_attachments = [
        FileAttachmentRequest.factory(token="file_token"),  # noqa: S106
    ]

    with (
        patch.object(
            facade,
            "build_media_attachments",
            new_callable=AsyncMock,
        ) as build_media_attachments_mock,
        patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        build_media_attachments_mock.return_value = uploaded_attachments
        result = await facade._build_media(input_files)

        expected_delay = UploadConfig().estimated_processing_delay(
            UploadType.FILE,
            len(data),
        )
        sleep_mock.assert_awaited_once_with(expected_delay)

    assert result == uploaded_attachments


async def test_build_media_only_requests(facade: DummyFacade) -> None:
    requests: list[MediaInput] = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
        VideoAttachmentRequest.factory(token="video_token"),  # noqa: S106
    ]

    with (
        patch.object(
            facade,
            "build_media_attachments",
            new_callable=AsyncMock,
        ) as build_media_attachments_mock,
        patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        result = await facade._build_media(requests)

        build_media_attachments_mock.assert_not_called()
        sleep_mock.assert_not_awaited()

    assert result == requests


async def test_build_media_mixed_order(facade: DummyFacade) -> None:
    input_file1 = BufferedInputFile.image(b"photo_bytes", "photo.jpg")
    request1 = VideoAttachmentRequest.factory(token="video_token")  # noqa: S106
    input_file2 = BufferedInputFile.image(b"photo_bytes2", "photo2.jpg")
    request2 = VideoAttachmentRequest.factory(token="video_token2")  # noqa: S106

    media: Sequence[MediaInput] = [input_file1, request1, input_file2, request2]

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

    with (
        patch.object(
            facade,
            "build_media_attachments",
            new_callable=AsyncMock,
        ) as upload_files_mock,
        patch(
            "asyncio.sleep",
            new_callable=AsyncMock,
        ) as sleep_mock,
    ):
        upload_files_mock.return_value = uploaded_attachments
        result = await facade._build_media(media)

        upload_files_mock.assert_called_once_with(
            [input_file1, input_file2],
            [len(b"photo_bytes"), len(b"photo_bytes2")],
        )
        sleep_mock.assert_not_awaited()

    assert result == expected_result


async def test_build_attachments_no_files(facade: DummyFacade) -> None:
    with patch.object(
        facade,
        "_build_media",
        new_callable=AsyncMock,
    ) as build_media_mock:
        result = await facade.build_attachments(base=[], files=None, keyboard=None)
        build_media_mock.assert_not_called()

    assert result == []


async def test_build_attachments_with_keyboard(facade: DummyFacade) -> None:
    button = CallbackButton(text="open", payload="payload")

    result = await facade.build_attachments(base=[], keyboard=((button,),), files=None)

    assert len(result) == 1
    attachment = result[0]
    assert isinstance(attachment, InlineKeyboardAttachmentRequest)
    assert attachment.payload.buttons == [[button]]


async def test_build_attachments_with_files(facade: DummyFacade) -> None:
    input_files = [BufferedInputFile.image(b"photo_bytes", "photo.jpg")]
    built_media = [
        PhotoAttachmentRequest.factory(token="photo_token"),  # noqa: S106
    ]

    with patch.object(
        facade,
        "_build_media",
        new_callable=AsyncMock,
    ) as build_media_mock:
        build_media_mock.return_value = built_media
        result = await facade.build_attachments(
            base=[],
            files=input_files,
            keyboard=None,
        )
        build_media_mock.assert_called_once_with(input_files)

    assert result == built_media


async def test_send_media_single_media_attachments_request(
    message_facade: DummyMessageFacade,
) -> None:
    request = PhotoAttachmentRequest.factory(token="photo_token")  # noqa: S106

    with patch.object(
        message_facade,
        "send_message",
        new_callable=AsyncMock,
    ) as send_message_mock:
        send_message_mock.return_value = AsyncMock()
        await message_facade.send_media(media=request)

        send_message_mock.assert_called_once()
        assert send_message_mock.call_args[1]["media"] == (request,)


async def test_build_media_attachments_for_all_known_upload_types(
    facade: DummyFacade,
) -> None:
    files = [
        BufferedInputFile.file(b"file", "file.bin"),
        BufferedInputFile.audio(b"audio", "audio.mp3"),
        BufferedInputFile.video(b"video", "video.mp4"),
        BufferedInputFile.image(b"image", "image.png"),
    ]

    with patch.object(facade, "upload_media", new_callable=AsyncMock) as upload_mock:
        upload_mock.side_effect = [
            (UploadType.FILE, "file-token"),
            (UploadType.AUDIO, "audio-token"),
            (UploadType.VIDEO, "video-token"),
            (UploadType.IMAGE, "image-token"),
        ]

        result = await facade.build_media_attachments(files)

    assert isinstance(result[0], FileAttachmentRequest)
    assert isinstance(result[1], AudioAttachmentRequest)
    assert isinstance(result[2], VideoAttachmentRequest)
    assert isinstance(result[3], PhotoAttachmentRequest)


async def test_build_media_attachments_skips_unknown_upload_type(
    facade: DummyFacade,
) -> None:
    with patch.object(facade, "upload_media", new_callable=AsyncMock) as upload_mock:
        upload_mock.return_value = (cast(UploadType, "unknown"), "token")

        result = await facade.build_media_attachments(
            [BufferedInputFile.file(b"file", "file.bin")],
        )

    assert result == []


async def test_upload_media_uses_resumable_when_configured(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.image(b"image", "image.png")
    bot_mock.upload_config = UploadConfig(method=UploadMethod.RESUMABLE)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(
            url="https://example.com/upload",
            token="endpoint-token",  # noqa: S106
        ),
    )
    bot_mock.upload_media_resumable = AsyncMock(
        return_value=UploadMediaResult(token="result-token"),  # noqa: S106
    )
    bot_mock.upload_media = AsyncMock()

    assert await facade.upload_media(file) == (UploadType.IMAGE, "endpoint-token")
    bot_mock.upload_media_resumable.assert_awaited_once_with(
        "https://example.com/upload",
        file,
        len(b"image"),
    )
    bot_mock.upload_media.assert_not_called()


async def test_upload_media_uses_single_when_configured(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.video(b"video", "video.mp4")
    bot_mock.upload_config = UploadConfig(method=UploadMethod.SINGLE)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com"),
    )
    bot_mock.upload_media = AsyncMock(
        return_value=UploadMediaResult(token="result-token"),  # noqa: S106
    )
    bot_mock.upload_media_resumable = AsyncMock()

    assert await facade.upload_media(file) == (UploadType.VIDEO, "result-token")
    bot_mock.upload_media.assert_awaited_once()
    bot_mock.upload_media_resumable.assert_not_called()


async def test_upload_media_single_retval_falls_back_to_endpoint_token(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.video(b"video", "video.mp4")
    bot_mock.upload_config = UploadConfig(method=UploadMethod.SINGLE)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(
            url="https://example.com",
            token="endpoint-token",  # noqa: S106
        ),
    )
    bot_mock.upload_media = AsyncMock(side_effect=RetvalReturnedServerException())

    assert await facade.upload_media(file) == (UploadType.VIDEO, "endpoint-token")


async def test_upload_media_auto_small_uses_single(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.file(b"tiny", "f.bin")
    bot_mock.upload_config = UploadConfig(method=UploadMethod.AUTO)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com"),
    )
    bot_mock.upload_media = AsyncMock(
        return_value=UploadMediaResult(token="single-token"),  # noqa: S106
    )
    bot_mock.upload_media_resumable = AsyncMock()

    assert await facade.upload_media(file) == (UploadType.FILE, "single-token")
    bot_mock.upload_media.assert_awaited_once()
    bot_mock.upload_media_resumable.assert_not_called()


async def test_upload_media_auto_large_uses_resumable(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.file(b"large-enough", "f.bin")
    bot_mock.upload_config = UploadConfig(
        method=UploadMethod.AUTO,
        resumable_threshold=4,
    )
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com"),
    )
    bot_mock.upload_media_resumable = AsyncMock(
        return_value=UploadMediaResult(token="resumable-token"),  # noqa: S106
    )
    bot_mock.upload_media = AsyncMock()

    assert await facade.upload_media(file) == (UploadType.FILE, "resumable-token")

    bot_mock.upload_media_resumable.assert_awaited_once()
    bot_mock.upload_media.assert_not_called()


async def test_upload_media_raises_without_any_token(
    facade: DummyFacade,
    bot_mock: AsyncMock,
) -> None:
    file = BufferedInputFile.audio(b"audio", "audio.mp3")
    bot_mock.upload_config = UploadConfig(method=UploadMethod.RESUMABLE)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com"),
    )
    bot_mock.upload_media_resumable = AsyncMock(return_value=None)

    with pytest.raises(RuntimeError, match="Could not get upload token"):
        await facade.upload_media(file)


@pytest.mark.parametrize(
    "method",
    [UploadMethod.SINGLE, UploadMethod.AUTO, UploadMethod.RESUMABLE],
)
async def test_upload_media_empty_file_rejected(
    facade: DummyFacade,
    bot_mock: AsyncMock,
    method: UploadMethod,
) -> None:
    file = BufferedInputFile.file(b"", "empty.bin")
    bot_mock.upload_config = UploadConfig(method=method)
    bot_mock.get_upload_url = AsyncMock(
        return_value=UploadEndpoint(url="https://example.com"),
    )
    bot_mock.upload_media = AsyncMock()
    bot_mock.upload_media_resumable = AsyncMock()

    with pytest.raises(ValueError, match="пустой файл"):
        await facade.upload_media(file)

    bot_mock.upload_media.assert_not_called()
    bot_mock.upload_media_resumable.assert_not_called()
