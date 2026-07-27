"""
Фильтры maxo. Алиас `maxo.routing.filters` для портирования ботов с `aiogram`.

`MagicFilter` и `MagicData` живут в `maxo.integrations.magic_filter`,
потому что `magic_filter` - опциональная зависимость.
"""

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
from maxo.routing.filters.payload import CallbackData, Payload
from maxo.routing.filters.state import StateFilter

__all__ = (
    "AlwaysFalseFilter",
    "AlwaysTrueFilter",
    "AndFilter",
    "BaseFilter",
    "CallbackData",
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
