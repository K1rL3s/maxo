import dataclasses
import typing
from functools import cache
from typing import TYPE_CHECKING, Any

from maxo.types.base import FacadeMaxoType

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


@cache
def _field_classes(class_: Any) -> dict[str, tuple[Any, ...]]:
    """
    Classes found at any depth of each field's type hint, `_bot` excluded.

    `list[Message] | None` -> `(Message,)`.
    """
    if not dataclasses.is_dataclass(class_):
        return {}

    fields = [field for field in dataclasses.fields(class_) if field.name != "_bot"]
    hints: dict[str, Any] = {}
    if any(isinstance(field.type, str) for field in dataclasses.fields(class_)):
        # `_bot` is hinted as the string "Bot | None"; `types/base.py` imports
        # `Bot` only under `TYPE_CHECKING`.
        from maxo.bot.bot import Bot  # noqa: PLC0415

        hints = typing.get_type_hints(class_, localns={"Bot": Bot})

    classes: dict[str, tuple[Any, ...]] = {}
    for field in fields:
        found: list[Any] = []
        stack = [hints.get(field.name, field.type)]
        while stack:
            hint = stack.pop()
            if isinstance(hint, type):
                found.append(hint)
            else:
                stack.extend(typing.get_args(hint))
        classes[field.name] = tuple(found)

    return classes


@cache
def _bot_fields(class_: Any) -> tuple[str, ...]:
    """
    Fields leading to a `FacadeMaxoType` at any depth.

    Terminates because the type graph is acyclic (`test_type_graph_is_acyclic`).
    """
    fields = []
    for name, classes in _field_classes(class_).items():
        leads_to_bot = any(
            issubclass(field_class, FacadeMaxoType) or _bot_fields(field_class)
            for field_class in classes
        )
        if leads_to_bot:
            fields.append(name)

    return tuple(fields)


def bind_bot[T](obj: T, bot: "Bot | None") -> T:
    """
    Bind the bot to every `FacadeMaxoType` in the tree under `obj`.

    Iterative DFS without `seen`: loaded data is a tree, nodes aren't shared.
    """
    stack: list[Any] = [obj]

    while stack:
        node = stack.pop()

        if isinstance(node, (list, tuple)):
            stack.extend(node)
            continue
        if isinstance(node, dict):  # UploadMediaResult.photos
            stack.extend(node.values())
            continue
        if isinstance(node, FacadeMaxoType):
            node._bot = bot  # noqa: SLF001

        for name in _bot_fields(node.__class__):
            child = getattr(node, name)
            if child is not None:
                stack.append(child)

    return obj
