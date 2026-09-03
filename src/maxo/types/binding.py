import dataclasses
import typing
from functools import cache
from typing import TYPE_CHECKING, Any, Optional, Self

from maxo.errors import AttributeIsEmptyError

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


class BotMixin:
    def __init__(self, bot: Optional["Bot"] = None) -> None:
        self._bot = bot

    def __post_init__(self) -> None:
        self._bot = None

    @property
    def bot(self) -> "Bot":
        if self._bot is not None:
            return self._bot

        raise AttributeIsEmptyError(
            obj=self,
            attr="_bot",
        )

    @bot.setter
    def bot(self, bot: Optional["Bot"]) -> None:
        bind_bot(self, bot)

    def as_(self, bot: Optional["Bot"]) -> Self:
        bind_bot(self, bot)
        return self


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
    Поля класса, внутри которых на любой глубине есть `BotMixin`.

    По ним `bind_bot` решает, спускаться ли в поле. Поле ведёт к боту, если его
    класс держит бота сам или содержит такое же поле глубже. Рекурсия конечна -
    граф типов ацикличен (`test_type_graph_is_acyclic`).
    """
    fields = []
    for name, classes in _field_classes(class_).items():
        leads_to_bot = any(
            issubclass(field_class, BotMixin) or _bot_fields(field_class)
            for field_class in classes
        )
        if leads_to_bot:
            fields.append(name)

    return tuple(fields)


def bind_bot[T](obj: T, bot: Optional["Bot"]) -> T:
    """
    Проставить бота всем `BotMixin` в дереве от `obj` вниз.

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
        if isinstance(node, BotMixin):
            node._bot = bot  # noqa: SLF001

        for name in _bot_fields(node.__class__):
            child = getattr(node, name)
            if child is not None:
                stack.append(child)

    return obj
