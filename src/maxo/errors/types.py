from typing import Any

from maxo.errors.base import MaxoError


class AttributeIsEmptyError(MaxoError, AttributeError):
    obj: Any
    attr: str

    def __str__(self) -> str:
        return (
            f"{self.obj.__class__.__name__}.{self.attr} "
            f"is empty ({getattr(self.obj, self.attr)!r})"
        )


class UnknownChatTypeError(MaxoError, ValueError):
    chat_type: Any

    def __str__(self) -> str:
        return f"Неизвестный тип чата: {self.chat_type}"
