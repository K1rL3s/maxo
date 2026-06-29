from datetime import UTC, datetime

from maxo.enums import ChatType
from maxo.types import Message, MessageBody, Recipient


def test_message_link() -> None:
    message = Message(
        body=MessageBody(mid="mid:edren_baton", seq=116341337478799028),
        recipient=Recipient(chat_id=-71196681472709, chat_type=ChatType.CHAT),
        timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
    )
    assert message.generated_url == "https://max.ru/c/-71196681472709/AZ1T1H0eHrQ"
