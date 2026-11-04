from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import unquote

VOID_TAGS = frozenset({"br", "img", "hr", "input", "meta", "link", "source", "wbr"})
BLOCK_TAGS = frozenset(
    {
        "div",
        "ul",
        "ol",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
        "table",
        "pre",
        "p",
    },
)
HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
SILENT_TAGS = ("svg", "button")
LOCAL_HREF_DEPTH = 2


@dataclass(slots=True, eq=False, repr=False)
class Element:
    tag: str
    attrs: dict[str, str]
    parent: "Element | None"
    children: "list[Element | str]" = field(default_factory=list)

    def has_class(self, name: str) -> bool:
        return name in self.attrs.get("class", "").split()

    def elements(self) -> "list[Element]":
        return [child for child in self.children if isinstance(child, Element)]

    def find(self, predicate: "Callable[[Element], bool]") -> "Element | None":
        for child in self.elements():
            if predicate(child):
                return child
            found = child.find(predicate)
            if found is not None:
                return found
        return None

    def find_class(self, name: str) -> "Element | None":
        return self.find(lambda element: element.has_class(name))

    def iter_class(self, name: str) -> "Iterator[Element]":
        for child in self.elements():
            if child.has_class(name):
                yield child
            yield from child.iter_class(name)

    def iter_tag(self, tag: str) -> "Iterator[Element]":
        for child in self.elements():
            if child.tag == tag:
                yield child
            else:
                yield from child.iter_tag(tag)

    def text(self) -> str:
        return "".join(
            child if isinstance(child, str) else child.text() for child in self.children
        )

    def own_text(self) -> str:
        return "".join(child for child in self.children if isinstance(child, str))

    def inline_markdown(self) -> str:
        inner = "".join(_inline(child) for child in self.children)
        if self.tag == "code":
            return f"`{self.text()}`"
        if self.tag in {"strong", "b"}:
            return f"**{inner}**"
        if self.tag in {"em", "i"}:
            return f"_{inner}_"
        if self.tag == "a":
            return f"[{inner}]({_normalize_href(self.attrs.get('href', ''))})"
        if self.tag == "br":
            return "<br/>"
        if self.tag in SILENT_TAGS:
            return ""
        return self.markdown() if self.tag in BLOCK_TAGS else inner

    def code_card_markdown(self) -> str:
        lang = self.find(
            lambda element: element.has_class("code-card__lang")
            or element.has_class("json-example__lang"),
        )
        code = self.find(lambda element: element.tag == "code")
        language = lang.text().strip().lower() if lang is not None else ""
        body = code.text() if code is not None else ""
        return f"```{language}\n{body.rstrip()}\n```"

    def markdown(self) -> str:
        parts: list[str] = []
        buffer: list[str] = []

        def flush() -> None:
            text = "".join(buffer).strip()
            if text:
                parts.append(text)
            buffer.clear()

        for child in self.children:
            if isinstance(child, str):
                buffer.append(child)
                continue
            block = child.block_markdown()
            if block is None:
                buffer.append(child.inline_markdown())
                continue
            flush()
            if block:
                parts.append(block)
        flush()
        return "\n\n".join(parts)

    def block_markdown(self) -> str | None:
        if self.has_class("code-card") or self.has_class("json-example"):
            return self.code_card_markdown()
        if self.tag in {"ul", "ol"}:
            items = [item for item in self.elements() if item.tag == "li"]
            return "\n".join(
                f"{f'{number}.' if self.tag == 'ol' else '-'} "
                + item.markdown().replace("\n\n", "\n").replace("\n", "\n  ")
                for number, item in enumerate(items, start=1)
            )
        if self.tag in HEADING_TAGS:
            title = self.find_class("linked-heading__text") or self
            return "#" * int(self.tag[1]) + " " + title.text().strip()
        if self.tag == "blockquote":
            return "\n".join(f"> {line}" for line in self.markdown().split("\n"))
        if self.tag == "table":
            return self.table_markdown()
        if self.tag == "hr":
            return "---"
        if self.tag in {"p", "div", "li", "pre"}:
            return self.markdown()
        return None

    def table_markdown(self) -> str:
        rows = [
            [
                cell.markdown().replace("\n", " ")
                for cell in row.elements()
                if cell.tag in {"td", "th"}
            ]
            for row in self.iter_tag("tr")
        ]
        if not rows:
            return ""
        lines = [
            "| " + " | ".join(rows[0]) + " |",
            "| " + " | ".join("---" for _ in rows[0]) + " |",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in rows[1:])
        return "\n".join(lines)


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#root", {}, None)
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent = self.current.parent
        if tag in BLOCK_TAGS and self.current.tag == "p" and parent is not None:
            self.current = parent
        element = Element(tag, _attributes(attrs), self.current)
        self.current.children.append(element)
        if tag not in VOID_TAGS:
            self.current = element

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.current.children.append(Element(tag, _attributes(attrs), self.current))

    def handle_endtag(self, tag: str) -> None:
        node: Element | None = self.current
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        self.current.children.append(data)


def parse_html(text: str) -> Element:
    builder = TreeBuilder()
    builder.feed(text)
    builder.close()
    return builder.root


def _attributes(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    return {name: value or "" for name, value in attrs}


def _inline(node: Element | str) -> str:
    return node if isinstance(node, str) else node.inline_markdown()


def _normalize_href(href: str) -> str:
    href = href.strip()
    if not href.startswith("/") or href.startswith("//"):
        return href
    path, _, fragment = href.partition("#")
    if path.count("/") > LOCAL_HREF_DEPTH:
        path = path.rstrip("/")
    if not fragment:
        return path
    return f"{path}#{unquote(fragment).replace(' ', '%20')}"
