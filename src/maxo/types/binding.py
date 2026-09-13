import dataclasses
import typing
from functools import cache
from typing import TYPE_CHECKING, Any, Optional

from maxo.types.facades.base import BaseMethodsFacade

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


@cache
def _field_classes(class_: Any) -> dict[str, tuple[Any, ...]]:
    """
    Для каждого поля - модели BaseMaxoType, спрятанные в хинте на любой глубине.

    Хинт разворачивается по аргументам: `list[Message] | None` -> `(Message,)`.
    """
    if not dataclasses.is_dataclass(class_):
        return {}

    fields = dataclasses.fields(class_)
    hints = (
        typing.get_type_hints(class_)
        if any(isinstance(field.type, str) for field in fields)
        else {}
    )

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
    Поля класса, внутри которых на любой глубине есть `BaseMethodsFacade`.

    По ним `bind_bot` решает, спускаться ли в поле. Поле ведёт к боту, если его
    класс держит бота сам или содержит такое же поле глубже. Рекурсия конечна:
    любой `MaxoType` - `BaseMethodsFacade`, так что `issubclass` замыкает её на
    первом же вложенном типе.
    """
    fields = []
    for name, classes in _field_classes(class_).items():
        leads_to_bot = any(
            issubclass(field_class, BaseMethodsFacade) or _bot_fields(field_class)
            for field_class in classes
        )
        if leads_to_bot:
            fields.append(name)

    return tuple(fields)


def bind_bot[T](obj: T, bot: Optional["Bot"]) -> T:
    """
    Проставить бота всем `BaseMethodsFacade` в дереве от `obj` вниз.

    DFS + стек, без `seen`: загрузчик строит дерево, общих узлов не бывает.
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
        if isinstance(node, BaseMethodsFacade):
            node._bot = bot  # noqa: SLF001

        for name in _bot_fields(node.__class__):
            child = getattr(node, name)
            if child is not None:
                stack.append(child)

    return obj
