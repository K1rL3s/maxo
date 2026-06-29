# ruff: noqa: E402

import warnings

warnings.warn(
    "Алиас `maxo.filters` сделан для удобного портирования ботов с `aiogram` "
    "и будет удален в будущих версиях. "
    "Пожалуйста, обновите импорты на 'from maxo.routing.filters import ...'",
    FutureWarning,
    stacklevel=2,
)

# `MagicFilter` and `MagicData` in maxo.integrations.magic_filter

from maxo.routing.filters.always import AlwaysFalseFilter, AlwaysTrueFilter
from maxo.routing.filters.base import BaseFilter
from maxo.routing.filters.command import Command, CommandObject, CommandStart
from maxo.routing.filters.deeplink import DeeplinkFilter
from maxo.routing.filters.exception import ExceptionMessageFilter, ExceptionTypeFilter
from maxo.routing.filters.logic import (
    AndFilter,
    InvertFilter,
    OrFilter,
    and_f,
    invert_f,
    or_f,
)
from maxo.routing.filters.payload import Payload
from maxo.routing.filters.state import StateFilter

__all__ = (
    "AlwaysFalseFilter",
    "AlwaysTrueFilter",
    "AndFilter",
    "BaseFilter",
    "Command",
    "CommandObject",
    "CommandStart",
    "DeeplinkFilter",
    "ExceptionMessageFilter",
    "ExceptionTypeFilter",
    "InvertFilter",
    "OrFilter",
    "Payload",
    "StateFilter",
    "and_f",
    "invert_f",
    "or_f",
)
