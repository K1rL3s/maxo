from typing import Any

from maxo.bot import methods
from maxo.bot.methods.base import MaxoMethod
from maxo.types import Attachments, Updates

_METHOD_ROOTS: tuple[type[MaxoMethod[Any]], ...] = tuple(
    dict.fromkeys(
        value
        for value in vars(methods).values()
        if isinstance(value, type)
        and issubclass(value, MaxoMethod)
        and value is not MaxoMethod
    ),
)

_DUMPED_ROOTS: tuple[Any, ...] = (*_METHOD_ROOTS, list[Attachments])

_LOADED_ROOTS: tuple[Any, ...] = (
    Updates,
    list[Attachments],
    *dict.fromkeys(method.__returning__ for method in _METHOD_ROOTS),
)


def warm_up() -> None:
    from maxo.serialization import get_retort  # noqa: PLC0415 - avoids import cycle

    retort = get_retort()
    for hint in _LOADED_ROOTS:
        retort.get_loader(hint)
    for hint in _DUMPED_ROOTS:
        retort.get_dumper(hint)
