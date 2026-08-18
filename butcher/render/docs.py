"""Docstring'и в стиле maxo: описание, ``Args:`` и ссылка на источник."""

import re

DOC_BASE_URL = "https://dev.max.ru"

# Относительные ссылки на доку: `](/docs-api/...)`, `](/docs-api#Якорь)`.
_LINK_PATTERN = re.compile(r"]\((/[^)]*)\)")
# Пункт списка: `- `/`-  `, но не `-H`, `--flag`, `-1`.
_LIST_ITEM = re.compile(r"-\s")
_DASHES = {
    0x2010: "-",
    0x2011: "-",
    0x2012: "-",
    0x2013: "-",
    0x2014: "-",
    0x2015: "-",
    0x2212: "-",
    0x00A0: " ",
}


def convert_links(text: str) -> str:
    """Развернуть относительные ссылки на документацию в абсолютные."""
    return _LINK_PATTERN.sub(rf"]({DOC_BASE_URL}\1)", text)


def normalize(text: str) -> str:
    """Все Unicode-тире - к обычному дефису, nbsp - к пробелу."""
    return text.translate(_DASHES)


def clean(text: str) -> str:
    """Подготовить кусок текста из спеки к вставке в docstring."""
    return convert_links(
        normalize(text)
        .strip()
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
        .replace("</br>", "\n")
        .replace('"""', "'''"),
    )


def _is_item(line: str) -> bool:
    return bool(_LIST_ITEM.match(line.lstrip(" ")))


def collapse_list_blanks(text: str) -> str:
    """Убрать пустые строки перед пунктами списка - печатаем списки плотно."""
    lines = text.split("\n")
    out: list[str] = []
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip(" ").startswith("```"):
            in_fence = not in_fence
        elif not in_fence and not line.strip():
            nxt = next((s for s in lines[i + 1 :] if s.strip()), "")
            if _is_item(nxt):
                continue
        out.append(line)
    return "\n".join(out)


def reflow_lists(text: str) -> str:
    """Сдвинуть пункты списка на +4, если он идёт вплотную за вводной."""
    # Отступ решаем по первому пункту и держим на весь список, иначе съедет
    # частично. Содержимое ``` не трогаем.
    out: list[str] = []
    in_fence = False
    prev = ""
    indent = False
    for line in text.split("\n"):
        stripped = line.lstrip(" ")
        if stripped.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and _LIST_ITEM.match(stripped):
            if not _is_item(prev):
                indent = bool(prev.strip())
            line = f"    {line}" if indent else line
        out.append(line)
        prev = line
    return "\n".join(out)


def build_parts(
    summary: str | None,
    description: str | None,
    parameters: list[tuple[str, str | None]],
    source_link: str | None = None,
    reflow: bool = False,
) -> list[str]:
    """Собрать строки docstring'а; ``reflow`` сдвигает пункты списка."""
    parts: list[str] = []

    if summary:
        parts.append(clean(summary))

    if description:
        if parts and parts[-1] != "":
            parts.append("")
        cleaned = collapse_list_blanks(clean(description))
        if reflow:
            cleaned = reflow_lists(cleaned)
        parts.extend(cleaned.split("\n"))

    if parameters:
        if parts and parts[-1] != "":
            parts.append("")
        parts.append("Args:")
        for name, raw in parameters:
            text = clean(raw).replace("\n\n", "\n") if raw else ""
            text = text.replace("\n", "\n        ")
            parts.append(f"    {name}: {text}")

    if source_link:
        if parts and parts[-1] != "":
            parts.append("")
        parts.append(f"Источник: {source_link}")

    return parts


def render(parts: list[str], indent: str = "    ") -> list[str]:
    """Готовые строки docstring'а с тройными кавычками (или пустой список)."""
    if not parts:
        return []

    lines: list[str] = []
    for part in parts:
        if part:
            lines.extend(f"{indent}{line}".rstrip() for line in part.split("\n"))
        else:
            lines.append("")
    while lines and not lines[-1].strip():
        lines.pop()

    if len(lines) == 1:
        return [f'{indent}"""{lines[0].strip()}"""']
    return [f'{indent}"""', *lines, f'{indent}"""']


def render_field(
    description: str | None,
    indent: str = "    ",
    reflow: bool = False,
) -> list[str]:
    """Docstring под полем: однострочный или блоком."""
    if not description:
        return []
    text = collapse_list_blanks(clean(description))
    if reflow:
        text = reflow_lists(text)
    if "\n" not in text:
        return [f'{indent}"""{text}"""']
    body = [f"{indent}{line}" if line else "" for line in text.split("\n")]
    return [f'{indent}"""', *body, f'{indent}"""']
