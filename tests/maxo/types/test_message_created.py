import pytest

from maxo.enums import ChatType, UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omitted
from maxo.types import Message, MessageBody, Recipient, User
from maxo.types.message_created import MessageCreated
from tests.constants import NOW


def create_message(text: str, user_id: int | None = 1) -> Message:
    sender = (
        User(
            user_id=user_id,
            first_name="Test",
            is_bot=False,
            last_activity_time=NOW,
        )
        if user_id is not None
        else Omitted()
    )
    return Message(
        body=MessageBody(seq=1, mid="1", text=text),
        recipient=Recipient(chat_id=1, chat_type=ChatType.PRIVATE),
        timestamp=NOW,
        sender=sender,
    )


def test_message_created_constructor() -> None:
    message = create_message("Hello")
    message_created = MessageCreated(
        message=message,
        user_locale="en-US",
        timestamp=NOW,
    )
    assert message_created.message is message
    assert message_created.user_locale == "en-US"
    assert message_created.type == UpdateType.MESSAGE_CREATED


def test_message_created_unsafe_user_locale_defined() -> None:
    message = create_message("Hello")
    message_created = MessageCreated(
        message=message,
        user_locale="en-US",
        timestamp=NOW,
    )
    assert message_created.unsafe_user_locale == "en-US"


def test_message_created_unsafe_user_locale_omitted() -> None:
    message = create_message("Hello")
    message_created = MessageCreated(
        message=message,
        user_locale=Omitted(),
        timestamp=NOW,
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = message_created.unsafe_user_locale


def test_message_created_text_property() -> None:
    message = create_message("Test message text")
    message_created = MessageCreated(
        message=message,
        timestamp=NOW,
    )
    assert message_created.text == "Test message text"


def test_message_created_user_id_property() -> None:
    message_with_user = create_message("Test", user_id=123)
    message_created_with_user = MessageCreated(
        message=message_with_user,
        timestamp=NOW,
    )
    assert message_created_with_user.user_id == 123

    message_no_user = create_message("Test", user_id=None)
    message_created_no_user = MessageCreated(
        message=message_no_user,
        timestamp=NOW,
    )
    assert message_created_no_user.user_id is None
