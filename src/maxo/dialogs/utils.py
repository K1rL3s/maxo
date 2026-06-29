from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from maxo.dialogs.api.internal import RawKeyboard
from maxo.types import (
    CallbackButton,
    MessageButton,
    Recipient,
    User,
)

CB_SEP = "\x1d"

REPLY_CALLBACK_SYMBOLS: str = (
    "\u200c"
    "\u200d"
    "\u2060"
    "\u2061"
    "\u2062"
    "\u2063"
    "\u2064"
    "\u00ad"
    "\U0001d173"
    "\U0001d174"
    "\U0001d175"
    "\U0001d176"
    "\U0001d177"
    "\U0001d178"
    "\U0001d179"
    "\U0001d17a"
)


def _encode_reply_callback_byte(byte: int) -> str:
    return (
        REPLY_CALLBACK_SYMBOLS[byte % len(REPLY_CALLBACK_SYMBOLS)]
        + REPLY_CALLBACK_SYMBOLS[byte // len(REPLY_CALLBACK_SYMBOLS)]
    )


def encode_reply_callback(data: str) -> str:
    bytes_data = data.encode("utf-8")
    return "".join(_encode_reply_callback_byte(byte) for byte in bytes_data)


def _decode_reply_callback_byte(little: str, big: str) -> int:
    return REPLY_CALLBACK_SYMBOLS.index(big) * len(
        REPLY_CALLBACK_SYMBOLS,
    ) + REPLY_CALLBACK_SYMBOLS.index(little)


def join_reply_callback(text: str, payload: str) -> str:
    return text + encode_reply_callback(payload)


def split_reply_callback(
    data: str | None,
) -> tuple[str | None, str | None]:
    if not data:
        return None, None
    text = data.rstrip(REPLY_CALLBACK_SYMBOLS)
    callback = data[len(text) :]
    return text, decode_reply_callback(callback)


def decode_reply_callback(data: str) -> str:
    bytes_data = bytes(
        _decode_reply_callback_byte(little, big)
        for little, big in zip(data[::2], data[1::2], strict=False)
    )
    return bytes_data.decode("utf-8")


def _transform_to_reply_button(
    button: CallbackButton | MessageButton,
) -> MessageButton:
    if isinstance(button, MessageButton):
        return button
    # if button.web_app:
    #     return KeyboardButton(text=button.text, web_app=button.web_app)
    if not button.payload:
        raise ValueError(
            "Cannot convert inline button without payload or web_app",
        )
    return MessageButton(
        text=join_reply_callback(
            text=button.text,
            payload=button.payload,
        ),
    )


def transform_to_reply_keyboard(
    keyboard: list[list[CallbackButton | MessageButton]],
) -> list[list[MessageButton]]:
    return [[_transform_to_reply_button(button) for button in row] for row in keyboard]


def is_recipient_loaded(recipient: Recipient) -> bool:
    """
    Check if chat is correctly loaded from telegram.

    For internal events it can be created with no data inside as a FakeChat
    """
    return not getattr(recipient, "fake", False)


def is_user_loaded(user: User) -> bool:
    """
    Check if user is correctly loaded from telegram.

    For internal events it can be created with no data inside as a FakeUser
    """
    return not getattr(user, "fake", False)


def intent_payload(
    intent_id: str,
    payload: str | None,
) -> str | None:
    if payload is None:
        return None
    prefix = intent_id + CB_SEP
    if payload.startswith(prefix):
        return payload
    return prefix + payload


intent_callback_data = intent_payload  # Подражание aiogram-dialogs


def add_intent_id(keyboard: RawKeyboard, intent_id: str) -> None:
    for row in keyboard:
        for button in row:
            if isinstance(button, CallbackButton):
                button.payload = intent_payload(
                    intent_id,
                    button.payload,
                )


def remove_intent_id(payload: str) -> tuple[str | None, str]:
    if CB_SEP in payload:
        intent_id, new_data = payload.split(CB_SEP, maxsplit=1)
        return intent_id, new_data
    return None, payload


P = ParamSpec("P")
R = TypeVar("R")


def add_exception_note(f: Callable[P, R]) -> Callable[P, R]:
    async def inner(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await f(self, *args, **kwargs)
        except Exception as e:
            e.add_note(f"at {self!r}")
            raise

    return inner
