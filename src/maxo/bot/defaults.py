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
from maxo.types import MaxoType


class BotDefaults(MaxoType):
    """Default values for bot API calls."""

    text_format: Omittable[TextFormat | None] = None
    """Default text format for messages"""
    disable_link_preview: Omittable[bool] = Omitted()
    """Default value for disable_link_preview parameter"""


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


# Methods with `format`/`disable_link_preview`
# `AnswerOnCallback.message` (`NewMessageBody`) is filled separately below
METHODS_WITH_DEFAULTS = (
    AnswerOnCallback,
    EditComment,
    EditMessage,
    SendComment,
    SendMessage,
)


def apply_defaults(method: _MethodT, defaults: BotDefaults) -> _MethodT:
    if not isinstance(method, METHODS_WITH_DEFAULTS):
        return method
    filled = _fill(method, defaults)
    if isinstance(filled, AnswerOnCallback) and is_defined(filled.message):
        filled = dataclasses.replace(filled, message=_fill(filled.message, defaults))
    return filled  # type: ignore[no-any-return]
