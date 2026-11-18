import pytest

from maxo.dialogs.api.entities import (
    MediaAttachment,
    MediaId,
    Stack,
)
from maxo.dialogs.api.entities.stack import id_to_str
from maxo.dialogs.api.exceptions import DialogStackOverflow, OutdatedIntent
from maxo.enums import AttachmentType
from maxo.fsm import State

MEDIA_ID = "media-id"
OTHER_MEDIA_ID = "other-media-id"


def test_outdated_intent_stores_stack_id() -> None:
    error = OutdatedIntent("stack", "outdated")

    assert str(error) == "outdated"
    assert error.stack_id == "stack"


def test_media_id_equality() -> None:
    media_id = MediaId(token=MEDIA_ID)

    assert media_id == MediaId(token=MEDIA_ID)
    assert media_id != MediaId(token=OTHER_MEDIA_ID)
    assert media_id != object()


def test_media_attachment_requires_source() -> None:
    with pytest.raises(ValueError, match="Neither url nor path nor media_id"):
        MediaAttachment(AttachmentType.IMAGE)


def test_media_attachment_file_id_alias_and_equality() -> None:
    media_id = MediaId(token=MEDIA_ID)
    attachment = MediaAttachment(
        AttachmentType.IMAGE,
        file_id=media_id,
        use_pipe=True,
        custom="value",
    )

    assert attachment.file_id == media_id
    assert attachment == MediaAttachment(
        AttachmentType.IMAGE,
        media_id=media_id,
        use_pipe=True,
        custom="value",
    )
    assert attachment != MediaAttachment(AttachmentType.VIDEO, media_id=media_id)
    assert attachment != object()


def test_stack_id_helpers_and_default_flag() -> None:
    assert id_to_str(0) == "0"
    assert Stack(_id="").default() is True
    assert Stack(_id="custom").default() is False


def test_stack_overflow() -> None:
    stack = Stack(intents=[str(index) for index in range(100)])

    with pytest.raises(DialogStackOverflow, match="Cannot open more dialogs"):
        stack.push(State(), {})
