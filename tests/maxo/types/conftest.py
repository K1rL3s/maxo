from maxo.enums import ChatType
from maxo.types import Callback, Message, MessageBody, Recipient, User
from tests.constants import NOW


def make_user() -> User:
    return User(
        user_id=1,
        first_name="Alice",
        last_name="Tester",
        name="Alice T.",
        username="alice",
        is_bot=False,
        last_activity_time=NOW,
    )


def make_message(**kwargs: object) -> Message:
    data = {
        "body": MessageBody(mid="mid", seq=7, text="hello"),
        "recipient": Recipient(chat_type=ChatType.CHAT, chat_id=10),
        "timestamp": NOW,
    }
    data.update(kwargs)
    return Message(**data)  # type: ignore[arg-type]


def make_callback() -> Callback:
    return Callback(
        callback_id="cb",
        timestamp=NOW,
        user=make_user(),
        payload="payload",
    )
