import pytest

from maxo.enums import VideoType
from maxo.enums.attachment_type import AttachmentType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted
from maxo.types import (
    Attachment,
    FileAttachmentPayload,
    MediaAttachmentPayload,
    VideoAttachment,
)
from maxo.types.attachments import AttachmentsRequests


def test_abstract_to_request() -> None:
    class MyAttachment(Attachment):
        def to_request(self) -> AttachmentsRequests:
            return Attachment.to_request(self)

    with pytest.raises(NotImplementedError):
        _ = MyAttachment(type=AttachmentType.IMAGE).to_request()


def test_video_attachment_unsafe_video_type_defined() -> None:
    video = VideoAttachment(
        payload=create_media_payload(),
        video_type=VideoType.VIDEO_MESSAGE,
    )

    assert video.unsafe_video_type == VideoType.VIDEO_MESSAGE


@pytest.mark.parametrize("video_type", [None, Omitted()])
def test_video_attachment_unsafe_video_type_empty(
    video_type: Omittable[VideoType | None],
) -> None:
    video = VideoAttachment(
        payload=create_media_payload(),
        video_type=video_type,
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_video_type


def test_media_attachment_payload_unsafe_id_defined() -> None:
    payload = create_media_payload(16922062446427)

    assert payload.unsafe_id == 16922062446427


@pytest.mark.parametrize("media_id", [None, Omitted()])
def test_media_attachment_payload_unsafe_id_empty(
    media_id: Omittable[int | None],
) -> None:
    payload = create_media_payload(media_id)

    with pytest.raises(AttributeIsEmptyError):
        _ = payload.unsafe_id


def test_file_attachment_payload_unsafe_file_id_defined() -> None:
    payload = create_file_payload(5399066140)

    assert payload.unsafe_file_id == 5399066140


@pytest.mark.parametrize("file_id", [None, Omitted()])
def test_file_attachment_payload_unsafe_file_id_empty(
    file_id: Omittable[int | None],
) -> None:
    payload = create_file_payload(file_id)

    with pytest.raises(AttributeIsEmptyError):
        _ = payload.unsafe_file_id


def create_media_payload(
    media_id: Omittable[int | None] = Omitted(),
) -> MediaAttachmentPayload:
    return MediaAttachmentPayload(
        url="url",
        token="token",  # noqa: S106
        id=media_id,
    )


def create_file_payload(file_id: Omittable[int | None]) -> FileAttachmentPayload:
    return FileAttachmentPayload(
        url="url",
        token="token",  # noqa: S106
        file_id=file_id,
    )
