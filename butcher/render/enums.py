"""Рендер файлов `maxo/enums/*.py`."""

import json

from butcher.overrides import EnumMember
from butcher.profile import Enum
from butcher.render import docs


def render(enum: Enum) -> str:
    extras = enum.extras
    header = ["from enum import StrEnum"]
    if extras.type_aliases:
        header.append("from typing import TypeAlias")

    lines = [*header, "", "", f"class {enum.name}(StrEnum):"]
    lines.extend(docs.render(docs.build_parts(None, enum.description, [], reflow=True)))
    if enum.description:
        lines.append("")

    lines.extend(
        _member_line(member)
        for member in (*extras.leading, *enum.members, *extras.trailing)
    )

    if extras.aliases:
        lines.append("")
        if extras.aliases_comment:
            lines.append(f"    # {extras.aliases_comment}")
        lines.extend(_member_line(alias) for alias in extras.aliases)

    for alias, comment in extras.type_aliases:
        lines.extend(["", "", f"{alias}: TypeAlias = {enum.name}  # {comment}"])

    return "\n".join(lines) + "\n"


def _member_line(member: EnumMember) -> str:
    # json.dumps даёт двойные кавычки - как требует `ruff format` в проекте.
    value = member.alias_of or json.dumps(member.value, ensure_ascii=False)
    line = f"    {member.name} = {value}"
    if member.comment:
        line += f"  # {member.comment}"
    return line
