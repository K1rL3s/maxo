import pytest

from maxo.enums import MarkupElementType
from maxo.types import StrikethroughMarkup
from maxo.types.emphasized_markup import EmphasizedMarkup
from maxo.types.strong_markup import StrongMarkup
from maxo.types.underline_markup import UnderlineMarkup
from maxo.types.user_mention_markup import UserMentionMarkup
from maxo.utils.formatting import (
    BlockQuote,
    Bold,
    Heading,
    Highlighted,
    Italic,
    Link,
    Mention,
    Monospaced,
    Strikethrough,
    Text,
    Underline,
    _apply_entity,
    as_key_value,
    as_line,
    as_list,
    as_marked_list,
    as_marked_section,
    as_numbered_list,
    as_numbered_section,
    as_section,
    sizeof,
)
from maxo.utils.text_decorations import html_decoration


class TestNode:
    @pytest.mark.parametrize(
        ("node", "result"),
        [
            (
                Text("test"),
                "test",
            ),
            (
                Bold("test"),
                "<b>test</b>",
            ),
            (
                Italic("test"),
                "<i>test</i>",
            ),
            (
                Underline("test"),
                "<u>test</u>",
            ),
            (
                Strikethrough("test"),
                "<s>test</s>",
            ),
            (
                Monospaced("test"),
                "<pre>test</pre>",
            ),
            (
                Link("test", url="https://example.com"),
                '<a href="https://example.com">test</a>',
            ),
            (
                Mention("test", user_id=42),
                '<a href="max://user/42">test</a>',
            ),
            (
                BlockQuote("test"),
                "<blockquote>test</blockquote>",
            ),
            (
                Heading("test"),
                "<h1>test</h1>",
            ),
            (
                Highlighted("test"),
                "<mark>test</mark>",
            ),
        ],
    )
    def test_render_plain_only(self, node: Text, result: str) -> None:
        text, entities = node.render()
        if node.type:
            assert len(entities) == 1
            entity = entities[0]
            assert entity.type == node.type

        content = html_decoration.unparse(text, entities)
        assert content == result

    def test_render_text(self) -> None:
        node = Text("Hello, ", "World", "!")
        text, entities = node.render()
        assert text == "Hello, World!"
        assert not entities

    def test_render_nested(self) -> None:
        node = Text(
            Text("Hello, ", Bold("World"), "!"),
            "\n",
            Text(Bold("This ", Underline("is"), " test", Italic("!"))),
        )
        text, entities = node.render()
        assert text == "Hello, World!\nThis is test!"
        assert entities == [
            StrongMarkup(from_=7, length=5),
            StrongMarkup(from_=14, length=13),
            UnderlineMarkup(from_=19, length=2),
            EmphasizedMarkup(from_=26, length=1),
        ]

    def test_as_html(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        assert node.as_html() == "Hello, <b>World</b>!"

    def test_as_markdown(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        assert node.as_markdown() == r"Hello, **World**\!"

    def test_replace(self) -> None:
        node0 = Text("test0", param0="test1")
        node1 = node0.replace("test1", "test2", param1="test1")
        assert node0._body != node1._body
        assert node0._params != node1._params
        assert "param1" not in node0._params
        assert "param1" in node1._params

    def test_add(self) -> None:
        node0 = Text("Hello")
        node1 = Bold("World")

        node2 = node0 + Text(", ") + node1 + "!"
        assert node0 != node2
        assert node1 != node2
        assert len(node0._body) == 1
        assert len(node1._body) == 1
        assert len(node2._body) == 3

        text, _ = node2.render()
        assert text == "Hello, World!"

    def test_getitem_position(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        with pytest.raises(TypeError):
            _ = node[2]  # type: ignore[index]

    def test_getitem_empty_slice(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[:]
        assert new_node is not node
        assert isinstance(new_node, Text)
        assert new_node._body == node._body

    def test_getitem_slice_zero(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[2:2]
        assert node is not new_node
        assert isinstance(new_node, Text)
        assert not new_node._body

    def test_getitem_slice_simple(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[2:10]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "llo, Wor"
        assert len(entities) == 1
        assert entities[0].type == MarkupElementType.STRONG

    def test_getitem_slice_inside_child(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[8:10]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "or"
        assert len(entities) == 1
        assert entities[0].type == MarkupElementType.STRONG

    def test_getitem_slice_tail(self) -> None:
        node = Text("Hello, ", Bold("World"), "!")
        new_node = node[12:13]
        assert isinstance(new_node, Text)
        text, entities = new_node.render()
        assert text == "!"
        assert not entities

    def test_from_entities(self) -> None:
        # Most of the cases covered by text_decorations module

        node = Strikethrough.from_entities(
            text="test1 test2 test3 test4 test5 test6",
            entities=[
                StrongMarkup(from_=6, length=23),
                UnderlineMarkup(from_=12, length=5),
                EmphasizedMarkup(from_=24, length=5),
            ],
        )
        assert len(node._body) == 3
        assert isinstance(node, Strikethrough)
        rendered = node.as_html()
        assert (
            rendered
            == "<s>test1 <b>test2 <u>test3</u> test4 <i>test5</i></b> test6</s>"
        )

    def test_pretty_string(self) -> None:
        node = Strikethrough.from_entities(
            text="X",
            entities=[
                UserMentionMarkup(
                    type=MarkupElementType.USER_MENTION,
                    from_=0,
                    length=1,
                    user_id=42,
                ),
            ],
        )
        assert (
            node.as_pretty_string(indent=True)
            == r"""Strikethrough(
    Mention(
        'X',
        user_id=42,
        user_link=<Omitted>
    )
)"""
        )


class TestUtils:
    def test_apply_entity(self) -> None:
        node = _apply_entity(
            StrongMarkup(from_=0, length=4),
            "test",
        )
        assert isinstance(node, Bold)
        assert node._body == ("test",)

    def test_as_line(self) -> None:
        node = as_line("test", "test", "test")
        assert isinstance(node, Text)
        assert len(node._body) == 4  # 3 + '\\n'

    def test_line_with_sep(self) -> None:
        node = as_line("test", "test", "test", sep=" ")
        assert isinstance(node, Text)
        assert len(node._body) == 6  # 3 + 2 * ' ' + '\\n'

    def test_as_line_single_element_with_sep(self) -> None:
        node = as_line("test", sep=" ")
        assert isinstance(node, Text)
        assert len(node._body) == 2  # 1 + '\\n'

    def test_as_list(self) -> None:
        node = as_list("test", "test", "test")
        assert isinstance(node, Text)
        assert len(node._body) == 5  # 3 + 2 * '\\n' between lines

    def test_as_marked_list(self) -> None:
        node = as_marked_list("test 1", "test 2", "test 3")
        assert node.as_html() == "- test 1\n- test 2\n- test 3"

    def test_as_numbered_list(self) -> None:
        node = as_numbered_list("test 1", "test 2", "test 3", start=5)
        assert node.as_html() == "5. test 1\n6. test 2\n7. test 3"

    def test_as_section(self) -> None:
        node = as_section("title", "test 1", "test 2", "test 3")
        assert node.as_html() == "title\ntest 1test 2test 3"

    def test_as_marked_section(self) -> None:
        node = as_marked_section("Section", "test 1", "test 2", "test 3")
        assert node.as_html() == "Section\n- test 1\n- test 2\n- test 3"

    def test_as_numbered_section(self) -> None:
        node = as_numbered_section("Section", "test 1", "test 2", "test 3", start=5)
        assert node.as_html() == "Section\n5. test 1\n6. test 2\n7. test 3"

    def test_as_key_value(self) -> None:
        node = as_key_value("key", "test 1")
        assert node.as_html() == "<b>key:</b> test 1"


class TestGetItemUnicode:
    """
    Tests for __getitem__ with multi-byte (UTF-16 surrogate pair) characters.

    Bug: `__getitem__` calls `len(node)` for plain string nodes which returns
    Unicode code points, while `len(self)` / `sizeof()` return UTF-16 code units.
    For emoji like "👋": len("👋") == 1 but sizeof("👋") == 2.
    This causes wrong offset tracking for all nodes that follow an emoji.
    """

    # --- helpers / sanity checks ---

    def test_sizeof_emoji(self) -> None:
        """Baseline: emoji takes 2 UTF-16 code units, not 1."""
        assert sizeof("👋") == 2
        assert len("👋") == 1  # code points - the source of the bug

    def test_len_of_node_with_emoji_string_body(self) -> None:
        """len(Text(...)) must return UTF-16 units (sizeof), not code points."""
        node = Text("hi", "👋", "!")
        # h=1 i=1 👋=2 !=1  →  5 UTF-16 units
        assert len(node) == 5

    # --- single string node ---

    def test_getitem_single_string_emoji_slice_over_emoji(self) -> None:
        """
        Text("hi👋!")[2:4] should return the 2 UTF-16 units that represent "👋",
        not "👋!" (which is what a plain code-point slice "hi👋!"[2:4] produces).
        """
        node = Text("hi👋!")
        # UTF-16 layout:  h(0) i(1) 👋(2,3) !(4)
        sliced = node[2:4]
        text, _ = sliced.render()
        assert text == "👋"

    def test_getitem_single_string_emoji_slice_after_emoji(self) -> None:
        """
        Text("hi👋!")[4:5] should return "!" (UTF-16 offset 4).
        With the len()-based bug the node_size is 4 (code points) so the
        iterator never reaches the "!" character.
        """
        node = Text("hi👋!")
        # UTF-16 layout:  h(0) i(1) 👋(2,3) !(4)
        sliced = node[4:5]
        text, _ = sliced.render()
        assert text == "!"

    # --- multiple string nodes ---

    def test_getitem_emoji_node_boundary(self) -> None:
        """
        Text("hi", "👋", "!")[2:4] must return only "👋".
        Bug: len("👋")==1 shifts the tracked position by 1 too few, so "!" is
        incorrectly included in the slice.
        """
        node = Text("hi", "👋", "!")
        # UTF-16 layout:  h(0) i(1) | 👋(2,3) | !(4)
        sliced = node[2:4]
        text, _ = sliced.render()
        assert text == "👋"

    def test_getitem_slice_starts_after_emoji_node(self) -> None:
        """
        Text("hi", "👋", "!")[4:5] must return "!".
        Bug: the position counter ends at 3 after the emoji node (instead of 4),
        so the "!" node is never visited.
        """
        node = Text("hi", "👋", "!")
        # UTF-16 layout:  h(0) i(1) | 👋(2,3) | !(4)
        sliced = node[4:5]
        text, _ = sliced.render()
        assert text == "!"

    def test_getitem_multiple_emojis_offset_accumulation(self) -> None:
        """
        Each emoji adds 2 UTF-16 units.  After two emoji the offset drift is 2.
        Text("a", "😀", "b", "😀", "c")[6:7] should return the second "c".
        UTF-16 layout: a(0) 😀(1,2) b(3) 😀(4,5) c(6)
        """
        node = Text("a", "😀", "b", "😀", "c")
        # len check
        assert len(node) == 7  # 1+2+1+2+1 = 7
        sliced = node[6:7]
        text, _ = sliced.render()
        assert text == "c"

    # --- Text sub-nodes (Bold etc.) are NOT affected ---

    def test_getitem_emoji_inside_bold_subnode_is_correct(self) -> None:
        """
        When the emoji lives inside a Text sub-node (Bold), len(Bold) already
        calls sizeof() correctly, so slicing must work fine.
        """
        node = Text("hi", Bold("👋"), "!")
        # UTF-16 layout:  h(0) i(1) | 👋(2,3) | !(4)
        sliced = node[2:4]
        text, entities = sliced.render()
        assert text == "👋"
        assert len(entities) == 1
        assert entities[0].type == MarkupElementType.STRONG

    def test_getitem_after_bold_emoji_subnode_is_correct(self) -> None:
        """Complement: slicing after an emoji Bold node must also work."""
        node = Text("hi", Bold("👋"), "!")
        sliced = node[4:5]
        text, _ = sliced.render()
        assert text == "!"

    # --- tests for entity sort stability (same offset) ---

    def test_from_entities_same_offset_outer_arrives_last(self) -> None:
        """
        from_entities must sort by (offset, -length) so that the wider
        (outer) entity wraps the narrower (inner) one, even when the
        shorter entity is listed first in the input.

        Without the fix the input order is preserved by stable sort and
        Italic would incorrectly become the outer wrapper:
          <i><b>Hello</b></i>lo  (wrong)

        With the fix (sort by -length as tie-breaker) Bold comes first:
          <b><i>Hel</i>lo</b>  (correct)
        """
        node = Text.from_entities(
            text="Hello",
            entities=[
                # shorter / inner - arrives first (wrong order)
                EmphasizedMarkup(from_=0, length=3),
                # longer / outer - arrives second
                StrongMarkup(from_=0, length=5),
            ],
        )
        assert node.as_html() == "<b><i>Hel</i>lo</b>"

    def test_from_entities_same_offset_outer_arrives_first(self) -> None:
        """
        Sanity check: from_entities works correctly when the wider entity
        already arrives before the narrower one at the same offset.
        """
        node = Text.from_entities(
            text="Hello",
            entities=[
                # longer / outer - arrives first (correct order)
                StrongMarkup(from_=0, length=5),
                # shorter / inner - arrives second
                EmphasizedMarkup(from_=0, length=3),
            ],
        )
        assert node.as_html() == "<b><i>Hel</i>lo</b>"

    def test_from_entities_same_offset_triple_nesting(self) -> None:
        """
        Three entities sharing offset=0 with descending lengths must nest
        from outermost to innermost regardless of input order.

        Correct: <s><b><i>Hi</i>!</b> there</s>
        """
        node = Text.from_entities(
            text="Hi! there",
            entities=[
                # innermost, shortest - arrives first
                EmphasizedMarkup(from_=0, length=2),
                # outermost, longest - arrives last
                StrikethroughMarkup(from_=0, length=9),
                # middle
                StrongMarkup(from_=0, length=3),
            ],
        )
        assert node.as_html() == "<s><b><i>Hi</i>!</b> there</s>"

    def test_render_same_offset_entities_ordered_by_descending_length(self) -> None:
        """
        render() must sort collected entities by (offset, -length) so that
        the outer (wider) entity appears before the inner (narrower) one
        when both start at the same offset.

        Without the fix inner entities are appended first during tree
        traversal and the stable sort preserves that wrong order.
        """
        # Bold covers "Hel" + "lo" = offsets 0-5; Italic covers "Hel" = offsets 0-3.
        node = Text(Bold(Italic("Hel"), "lo"))
        _, entities = node.render()

        bold_idx = next(
            i for i, e in enumerate(entities) if e.type == MarkupElementType.STRONG
        )
        italic_idx = next(
            i for i, e in enumerate(entities) if e.type == MarkupElementType.EMPHASIZED
        )

        # Outer (Bold, length=5) must come before inner (Italic, length=3)
        assert bold_idx < italic_idx, (
            "Bold (outer, length=5) must be sorted before Italic (inner, length=3) "
            "when both share offset=0"
        )
        # Verify the HTML round-trip is correct
        assert node.as_html() == "<b><i>Hel</i>lo</b>"

    def test_render_as_html_same_offset_nested(self) -> None:
        """
        as_html() end-to-end: Bold wrapping Italic at the same start offset
        must produce correct HTML after the render() sort fix.
        """
        assert Bold(Italic("x"), "y").as_html() == "<b><i>x</i>y</b>"
        assert Bold(Italic("foo"), "bar").as_html() == "<b><i>foo</i>bar</b>"
