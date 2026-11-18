import dataclasses
import sys
import typing
from functools import cache
from typing import TYPE_CHECKING, Any

from adaptix.type_tools import exec_type_checking

from maxo.types.base import FacadeMaxoType

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


@cache
def _field_classes(class_: type) -> dict[str, tuple[type, ...]]:
    if not dataclasses.is_dataclass(class_):
        return {}

    try:
        hints = typing.get_type_hints(class_)
    except NameError:
        for module_name in dict.fromkeys(base.__module__ for base in class_.__mro__):
            if module_name != "builtins":
                exec_type_checking(sys.modules[module_name])
        hints = typing.get_type_hints(class_)

    result: dict[str, tuple[type, ...]] = {}
    for field in dataclasses.fields(class_):
        classes: list[type] = []
        stack = [hints[field.name]]
        while stack:
            value = stack.pop()
            if isinstance(value, type):
                classes.append(value)
            else:
                stack.extend(typing.get_args(value))
        result[field.name] = tuple(classes)
    return result


@cache
def _leads_to_facade(class_: Any) -> bool:
    stack = [class_]
    seen: set[Any] = set()
    while stack:
        current = stack.pop()
        if issubclass(current, FacadeMaxoType):
            return True
        if current in seen:
            continue
        seen.add(current)
        for classes in _field_classes(current).values():
            stack.extend(classes)
    return False


@cache
def _fields_to_bind(class_: Any) -> tuple[str, ...]:
    return tuple(
        name
        for name, classes in _field_classes(class_).items()
        if any(map(_leads_to_facade, classes))
    )


def bind_bot[T](obj: T, bot: "Bot | None") -> T:
    """Set `bot` on every `FacadeMaxoType` under `obj`; `seen` handles cycles."""
    stack: list[Any] = [obj]
    seen: set[int] = set()

    while stack:
        node = stack.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))

        if isinstance(node, (list, tuple)):
            stack.extend(node)
        elif isinstance(node, dict):  # UploadMediaResult.photos
            stack.extend(node.values())
        else:
            if isinstance(node, FacadeMaxoType):
                node._bot = bot  # noqa: SLF001
            for name in _fields_to_bind(node.__class__):
                child = getattr(node, name)
                if child is not None:
                    stack.append(child)

    return obj
