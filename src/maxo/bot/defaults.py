import dataclasses
from typing import Any, TypeVar

from maxo.bot.methods import (
    AnswerOnCallback,
    EditComment,
    EditMessage,
    SendComment,
    SendMessage,
)
from maxo.enums import TextFormat
from maxo.omit import Omittable, Omitted, is_defined, is_omitted
from maxo.types import MaxoType, NewCommentBody


class BotDefaults(MaxoType):
    """Default values for bot API calls."""

    text_format: Omittable[TextFormat | None] = None
    """Default text format for messages"""
    disable_link_preview: Omittable[bool | None] = Omitted()
    """Default value for disable_link_preview parameter"""

    def __post_init__(self) -> None:
        # API ожидает Omittable[bool]. None здесь для совместимости с maxo 0.5.0
        if self.disable_link_preview is None:
            self.disable_link_preview = Omitted()


_MethodT = TypeVar("_MethodT")


def _fill(obj: Any, defaults: BotDefaults) -> Any:
    if hasattr(obj, "format") and is_omitted(obj.format):
        obj = dataclasses.replace(obj, format=defaults.text_format)
    if hasattr(obj, "disable_link_preview") and is_omitted(obj.disable_link_preview):
        obj = dataclasses.replace(
            obj,
            disable_link_preview=defaults.disable_link_preview,
        )
    return obj


def apply_defaults(method: _MethodT, defaults: BotDefaults) -> _MethodT:
    if isinstance(
        method,
        (SendMessage, EditMessage, SendComment, EditComment, NewCommentBody),
    ):
        return _fill(method, defaults)  # type: ignore[no-any-return]
    if isinstance(method, AnswerOnCallback) and is_defined(method.message):
        return dataclasses.replace(
            method,
            message=_fill(method.message, defaults),
        )
    return method
