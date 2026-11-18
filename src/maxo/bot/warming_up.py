from typing import Any

from maxo.bot import methods
from maxo.bot.methods.base import MaxoMethod
from maxo.types import Attachments, Updates

_METHODS: tuple[type[MaxoMethod[Any]], ...] = tuple(
    dict.fromkeys(
        value
        for value in vars(methods).values()
        if isinstance(value, type)
        and issubclass(value, MaxoMethod)
        and value is not MaxoMethod
    ),
)

_DUMPED_HINTS: tuple[Any, ...] = (*_METHODS, list[Attachments])

_LOADED_HINTS: tuple[Any, ...] = (
    Updates,
    list[Attachments],
    *dict.fromkeys(method.__returning__ for method in _METHODS),
)


def warm_up() -> None:
    from maxo.serialization import get_retort  # noqa: PLC0415 - avoids import cycle

    retort = get_retort()
    for hint in _LOADED_HINTS:
        retort.get_loader(hint)
    for hint in _DUMPED_HINTS:
        retort.get_dumper(hint)
