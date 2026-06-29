"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/formatting.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import dataclasses
import textwrap
from collections.abc import Generator, Iterable, Iterator
from typing import Any, ClassVar, Self, TypeAlias

from maxo.enums import MarkupElementType
from maxo.types.emphasized_markup import EmphasizedMarkup
from maxo.types.link_markup import LinkMarkup
from maxo.types.markup_element import MarkupElement
from maxo.types.markup_elements import MarkupElements
from maxo.types.monospaced_markup import MonospacedMarkup
from maxo.types.strikethrough_markup import StrikethroughMarkup
from maxo.types.strong_markup import StrongMarkup
from maxo.types.underline_markup import UnderlineMarkup
from maxo.types.user_mention_markup import UserMentionMarkup
from maxo.utils.text_decorations import (
    add_surrogates,
    html_decoration,
    markdown_decoration,
    remove_surrogates,
)

_MARKUP_MAP: dict[MarkupElementType, type[MarkupElements]] = {
    MarkupElementType.STRONG: StrongMarkup,
    MarkupElementType.EMPHASIZED: EmphasizedMarkup,
    MarkupElementType.UNDERLINE: UnderlineMarkup,
    MarkupElementType.STRIKETHROUGH: StrikethroughMarkup,
    MarkupElementType.MONOSPACED: MonospacedMarkup,
    MarkupElementType.LINK: LinkMarkup,
    MarkupElementType.USER_MENTION: UserMentionMarkup,
}

NodeType: TypeAlias = Any


def sizeof(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2


class Text(Iterable[NodeType]):
    type: ClassVar[MarkupElementType | None] = None

    __slots__ = ("_body", "_params")

    def __init__(
        self,
        *body: NodeType,
        **params: Any,
    ) -> None:
        self._body: tuple[NodeType, ...] = body
        self._params: dict[str, Any] = params

    @classmethod
    def from_entities(cls, text: str, entities: list[MarkupElements]) -> "Text":
        return cls(
            *_unparse_entities(
                text=add_surrogates(text),
                entities=(
                    sorted(
                        entities,
                        key=lambda item: (item.offset, -item.length),
                    )
                    if entities
                    else []
                ),
            ),
        )

    def render(
        self,
        *,
        _offset: int = 0,
        _sort: bool = True,
        _collect_entities: bool = True,
    ) -> tuple[str, list[MarkupElements]]:
        """Render elements tree as text with entities list."""
        text = ""
        entities = []
        offset = _offset

        for node in self._body:
            if not isinstance(node, Text):
                node = str(node)
                text += node
                offset += sizeof(node)
            else:
                node_text, node_entities = node.render(
                    _offset=offset,
                    _sort=False,
                    _collect_entities=_collect_entities,
                )
                text += node_text
                offset += sizeof(node_text)
                if _collect_entities:
                    entities.extend(node_entities)

        if _collect_entities and self.type:
            entities.append(
                self._render_entity(offset=_offset, length=offset - _offset),
            )

        if _collect_entities and _sort:
            entities.sort(key=lambda entity: (entity.offset, -entity.length))

        return text, entities

    def _render_entity(self, *, offset: int, length: int) -> MarkupElements:
        if self.type is None:
            raise ValueError("Node without type can't be rendered as entity")

        markup_class: type[MarkupElements] = _MARKUP_MAP.get(self.type, MarkupElement)
        return markup_class(
            type=self.type,
            from_=offset,
            length=length,
            **self._params,
        )

    def as_kwargs(
        self,
        *,
        text_key: str = "text",
        replace_format: bool = True,
        format_key: str = "format",
    ) -> dict[str, Any]:
        """
        Render element tree as keyword arguments for usage in an API call.

        .. code-block:: python

            entities = Text(...)
            await facade.answer_text(**entities.as_kwargs())
        """
        text_value, _ = self.render()
        result: dict[str, Any] = {text_key: text_value}
        if replace_format:
            result[format_key] = None
        return result

    def as_html(self) -> str:
        """Render elements tree as HTML markup."""
        text, entities = self.render()
        return html_decoration.unparse(text, entities)

    def as_markdown(self) -> str:
        """Render elements tree as Markdown markup."""
        text, entities = self.render()
        return markdown_decoration.unparse(text, entities)

    def replace(self, *args: Any, **kwargs: Any) -> Self:
        return type(self)(*args, **{**self._params, **kwargs})

    def as_pretty_string(self, indent: bool = False) -> str:
        sep = ",\n" if indent else ", "
        body = sep.join(
            (
                item.as_pretty_string(indent=indent)
                if isinstance(item, Text)
                else repr(item)
            )
            for item in self._body
        )
        params = sep.join(
            f"{k}={v!r}" for k, v in self._params.items() if v is not None
        )

        args = []
        if body:
            args.append(body)
        if params:
            args.append(params)

        args_str = sep.join(args)
        if indent:
            args_str = textwrap.indent("\n" + args_str + "\n", "    ")
        return f"{type(self).__name__}({args_str})"

    def __add__(self, other: NodeType) -> "Text":
        if (
            isinstance(other, Text)
            and other.type == self.type
            and self._params == other._params
        ):
            return type(self)(*self, *other, **self._params)
        if type(self) is Text and isinstance(other, str):
            return type(self)(*self, other, **self._params)
        return Text(self, other)

    def __iter__(self) -> Iterator[NodeType]:
        yield from self._body

    def __len__(self) -> int:
        text, _ = self.render(_collect_entities=False)
        return sizeof(text)

    def __getitem__(self, item: slice) -> "Text":
        if not isinstance(item, slice):
            raise TypeError("Can only be sliced")
        if (item.start is None or item.start == 0) and item.stop is None:
            return self.replace(*self._body)
        start = 0 if item.start is None else item.start
        stop = len(self) if item.stop is None else item.stop
        if start == stop:
            return self.replace()

        nodes = []
        position = 0

        for node in self._body:
            node_size = sizeof(node) if isinstance(node, str) else len(node)
            current_position = position
            position += node_size
            if position < start:
                continue
            if current_position > stop:
                break
            a = max((0, start - current_position))
            b = min((node_size, stop - current_position))

            if isinstance(node, str):
                new_node = remove_surrogates(add_surrogates(node)[a * 2 : b * 2])
            else:
                new_node = node[a:b]

            if not new_node:
                continue
            nodes.append(new_node)

        return self.replace(*nodes)


class Bold(Text):
    type = MarkupElementType.STRONG


class Italic(Text):
    type = MarkupElementType.EMPHASIZED


class Underline(Text):
    type = MarkupElementType.UNDERLINE


class Strikethrough(Text):
    type = MarkupElementType.STRIKETHROUGH


class BlockQuote(Text):
    type = MarkupElementType.QUOTE


class Monospaced(Text):
    type = MarkupElementType.MONOSPACED


class Link(Text):
    type = MarkupElementType.LINK

    def __init__(self, *body: NodeType, url: str, **params: Any) -> None:
        super().__init__(*body, url=url, **params)


class Mention(Text):
    type = MarkupElementType.USER_MENTION

    def __init__(self, *body: NodeType, user_id: int, **params: Any) -> None:
        super().__init__(*body, user_id=user_id, **params)


class Heading(Text):
    type = MarkupElementType.HEADING


class Highlighted(Text):
    type = MarkupElementType.HIGHLIGHTED


NODE_TYPES: dict[MarkupElementType | None, type[Text]] = {
    Text.type: Text,
    BlockQuote.type: BlockQuote,
    Bold.type: Bold,
    Italic.type: Italic,
    Underline.type: Underline,
    Strikethrough.type: Strikethrough,
    Monospaced.type: Monospaced,
    Link.type: Link,
    Mention.type: Mention,
    Heading.type: Heading,
    Highlighted.type: Highlighted,
}


def _apply_entity(entity: MarkupElements, *nodes: NodeType) -> NodeType:
    """Apply single entity to text."""
    node_type = NODE_TYPES.get(entity.type, Text)

    entity_dict = dataclasses.asdict(entity)
    for key in ("type", "from_", "length"):
        entity_dict.pop(key, None)

    return node_type(
        *nodes,
        **entity_dict,
    )


def _unparse_entities(
    text: bytes,
    entities: list[MarkupElements],
    offset: int | None = None,
    length: int | None = None,
) -> Generator[NodeType, None, None]:
    if offset is None:
        offset = 0
    if length is None:
        length = len(text)

    for index, entity in enumerate(entities):
        if entity.offset * 2 < offset:
            continue
        if entity.offset * 2 > offset:
            yield remove_surrogates(text[offset : entity.offset * 2])
        start = entity.offset * 2
        offset = entity.offset * 2 + entity.length * 2

        sub_entities = list(
            filter(lambda e: e.offset * 2 < offset, entities[index + 1 :]),
        )
        yield _apply_entity(
            entity,
            *_unparse_entities(text, sub_entities, offset=start, length=offset),
        )

    if offset < length:
        yield remove_surrogates(text[offset:length])


def as_line(*items: NodeType, end: str = "\n", sep: str = "") -> Text:
    r"""Wrap multiple nodes into line with :code:`\n` at the end of line."""
    if not items:
        return Text(end)

    if sep:
        nodes = []
        for item in items[:-1]:
            nodes.extend([item, sep])
        nodes.extend([items[-1], end])
    else:
        nodes = [*items, end]
    return Text(*nodes)


def as_list(*items: NodeType, sep: str = "\n") -> Text:
    """Wrap each element to separated lines."""
    if not items:
        return Text()

    nodes = []
    for item in items[:-1]:
        nodes.extend([item, sep])
    nodes.append(items[-1])
    return Text(*nodes)


def as_marked_list(*items: NodeType, marker: str = "- ") -> Text:
    """Wrap elements as marked list."""
    return as_list(*(Text(marker, item) for item in items))


def as_numbered_list(*items: NodeType, start: int = 1, fmt: str = "{}. ") -> Text:
    """Wrap elements as numbered list."""
    return as_list(
        *(Text(fmt.format(index), item) for index, item in enumerate(items, start)),
    )


def as_section(title: NodeType, *body: NodeType) -> Text:
    """Wrap elements as simple section, section has title and body."""
    return Text(title, "\n", *body)


def as_marked_section(
    title: NodeType,
    *body: NodeType,
    marker: str = "- ",
) -> Text:
    """Wrap elements as section with marked list."""
    return as_section(title, as_marked_list(*body, marker=marker))


def as_numbered_section(
    title: NodeType,
    *body: NodeType,
    start: int = 1,
    fmt: str = "{}. ",
) -> Text:
    """Wrap elements as section with numbered list."""
    return as_section(title, as_numbered_list(*body, start=start, fmt=fmt))


def as_key_value(key: NodeType, value: NodeType) -> Text:
    """Wrap elements pair as key-value line. (:code:`<b>{key}:</b> {value}`)."""
    return Text(Bold(key, ":"), " ", value)
