"""Рендер файлов-объединений в `maxo/types`: `attachments.py`, `updates.py` и т.п."""

from butcher.profile import Union, Unions
from butcher.render import imports


def render(unions: Unions) -> str:
    header = ["from typing import TypeAlias"] if _annotated(unions) else []
    lines = [*header, imports.render(unions.imports), ""]
    lines.extend(
        f"{alias.name}{_annotation(alias)} = {' | '.join(alias.members)}"
        for alias in unions.aliases
    )
    return "\n".join(lines) + "\n"


def _annotated(unions: Unions) -> bool:
    return any(alias.annotate for alias in unions.aliases)


def _annotation(alias: Union) -> str:
    return ": TypeAlias" if alias.annotate else ""
