import pytest

from maxo.enums import MarkupElementType
from maxo.types import (
    EmphasizedMarkup,
    HeadingMarkup,
    HighlightedMarkup,
    LinkMarkup,
    MarkupElement,
    MarkupElements,
    MonospacedMarkup,
    StrikethroughMarkup,
    StrongMarkup,
    UnderlineMarkup,
    UserMentionMarkup,
)
from maxo.utils.text_decorations import (
    TextDecoration,
    html_decoration,
    markdown_decoration,
)


class TestTextDecoration:
    @pytest.mark.parametrize(
        ("decorator", "entity", "result"),
        [
            (
                html_decoration,
                LinkMarkup(from_=0, length=4, url="https://aiogram.dev"),
                '<a href="https://aiogram.dev">test</a>',
            ),
            (html_decoration, StrongMarkup(from_=0, length=4), "<b>test</b>"),
            (html_decoration, EmphasizedMarkup(from_=0, length=4), "<i>test</i>"),
            (html_decoration, MonospacedMarkup(from_=0, length=4), "<pre>test</pre>"),
            (html_decoration, UnderlineMarkup(from_=0, length=4), "<u>test</u>"),
            (html_decoration, StrikethroughMarkup(from_=0, length=4), "<s>test</s>"),
            (
                html_decoration,
                UserMentionMarkup(from_=0, length=4, user_id=42),
                '<a href="max://user/42">test</a>',
            ),
            (
                markdown_decoration,
                LinkMarkup(from_=0, length=4, url="https://aiogram.dev"),
                "[test](https://aiogram.dev)",
            ),
            (markdown_decoration, StrongMarkup(from_=0, length=4), "**test**"),
            (markdown_decoration, EmphasizedMarkup(from_=0, length=4), "_test_"),
            (markdown_decoration, MonospacedMarkup(from_=0, length=4), "`test`"),
            (markdown_decoration, UnderlineMarkup(from_=0, length=4), "++test++"),
            (markdown_decoration, StrikethroughMarkup(from_=0, length=4), "~~test~~"),
            (
                markdown_decoration,
                UserMentionMarkup(from_=0, length=4, user_id=42),
                "[test](max://user/42)",
            ),
            (
                html_decoration,
                MarkupElement(type=MarkupElementType.QUOTE, from_=0, length=4),
                "<blockquote>test</blockquote>",
            ),
            (
                markdown_decoration,
                MarkupElement(type=MarkupElementType.QUOTE, from_=0, length=4),
                "> test",
            ),
            (
                html_decoration,
                HeadingMarkup(from_=0, length=4),
                "<h1>test</h1>",
            ),
            (
                markdown_decoration,
                HeadingMarkup(from_=0, length=4),
                "# test",
            ),
            (
                html_decoration,
                HighlightedMarkup(from_=0, length=4),
                "<mark>test</mark>",
            ),
            (
                markdown_decoration,
                HighlightedMarkup(from_=0, length=4),
                "^^test^^",
            ),
        ],
    )
    def test_apply_single_entity(
        self,
        decorator: TextDecoration,
        entity: MarkupElements,
        result: str,
    ) -> None:
        assert decorator.apply_entity(entity, "test") == result

    def test_unknown_apply_entity(self) -> None:
        assert (
            html_decoration.apply_entity(
                MarkupElement(type="unknown", from_=0, length=4),  # type: ignore[arg-type]
                "<test>",
            )
            == "&lt;test&gt;"
        )

    @pytest.mark.parametrize(
        ("decorator", "before", "after"),
        [
            (html_decoration, "test", "test"),
            (html_decoration, "test < test", "test &lt; test"),
            (html_decoration, "test > test", "test &gt; test"),
            (html_decoration, "test & test", "test &amp; test"),
            (html_decoration, "test @ test", "test @ test"),
            (markdown_decoration, "test", "test"),
            (markdown_decoration, "(test)", "\\(test\\)"),
            (markdown_decoration, "test ` test", "test \\` test"),
            (markdown_decoration, "test * test", "test \\* test"),
            (markdown_decoration, "test _ test", "test \\_ test"),
            (markdown_decoration, "x^2 + y^2", "x\\^2 \\+ y\\^2"),
        ],
    )
    def test_quote(self, decorator: TextDecoration, before: str, after: str) -> None:
        assert decorator.quote(before) == after

    @pytest.mark.parametrize(
        ("decorator", "text", "entities", "result"),
        [
            (html_decoration, "test", None, "test"),
            (html_decoration, "test", (), "test"),
            (
                html_decoration,
                "test1 test2 test3 test4 test5 test6 test7",
                (
                    StrongMarkup(from_=6, length=29),
                    UnderlineMarkup(from_=12, length=5),
                    EmphasizedMarkup(from_=24, length=5),
                ),
                "test1 <b>test2 <u>test3</u> test4 <i>test5</i> test6</b> test7",
            ),
            (
                html_decoration,
                "test1 test2 test3 test4 test5",
                (
                    StrongMarkup(from_=6, length=17),
                    UnderlineMarkup(from_=12, length=5),
                ),
                "test1 <b>test2 <u>test3</u> test4</b> test5",
            ),
            (
                html_decoration,
                "test1 test2 test3 test4",
                (
                    StrongMarkup(from_=6, length=11),
                    UnderlineMarkup(from_=12, length=5),
                ),
                "test1 <b>test2 <u>test3</u></b> test4",
            ),
            (
                html_decoration,
                "test1 test2 test3",
                (StrongMarkup(from_=6, length=5),),
                "test1 <b>test2</b> test3",
            ),
            (
                html_decoration,
                "test1 test2",
                (StrongMarkup(from_=0, length=5),),
                "<b>test1</b> test2",
            ),
            (
                html_decoration,
                "strike bold",
                (
                    StrikethroughMarkup(from_=0, length=6),
                    StrongMarkup(from_=7, length=4),
                ),
                "<s>strike</s> <b>bold</b>",
            ),
            (
                html_decoration,
                "test",
                (
                    StrikethroughMarkup(from_=0, length=4),
                    StrongMarkup(from_=0, length=4),
                ),
                "<s><b>test</b></s>",
            ),
            (
                html_decoration,
                "strikeboldunder",
                (
                    StrikethroughMarkup(from_=0, length=15),
                    StrongMarkup(from_=6, length=9),
                    UnderlineMarkup(from_=10, length=5),
                ),
                "<s>strike<b>bold<u>under</u></b></s>",
            ),
            # Когда у юзеров появятся юзернеймы, поддерживать их
            # Сейчас есть только user_id
            # (
            #     html_decoration,
            #     "@username",
            #     (
            #         UserMentionMarkup(from_=0, length=9),
            #         StrongMarkup(from_=0, length=9),
            #     ),
            #     "<b>@username</b>",
            # ),
            (
                html_decoration,
                "test te👍🏿st test",
                (StrongMarkup(from_=5, length=8),),
                "test <b>te👍🏿st</b> test",
            ),
            (
                html_decoration,
                "👋🏾 Hi!",
                (StrongMarkup(from_=0, length=8),),
                "<b>👋🏾 Hi!</b>",
            ),
        ],
    )
    def test_unparse(
        self,
        decorator: TextDecoration,
        text: str,
        entities: list[MarkupElements] | None,
        result: str,
    ) -> None:
        assert decorator.unparse(text, entities) == result


class TestMarkdownDecorationBlockquote:
    """Regression tests for #304: `MarkdownDecoration.blockquote` used to
    drop content on `str.splitlines()` edge cases (empty string, trailing
    newline), unlike `HtmlDecoration.blockquote` which is symmetric."""

    def test_empty_string_is_not_dropped(self) -> None:
        # Previously: "".splitlines() == [] -> "" (quote vanished).
        assert markdown_decoration.blockquote("") == "> "

    def test_trailing_newline_is_preserved(self) -> None:
        # Previously: "a\n".splitlines() == ["a"] -> "> a" (trailing
        # newline silently eaten).
        assert markdown_decoration.blockquote("a\n") == "> a\n> "

    def test_multiline_value(self) -> None:
        assert markdown_decoration.blockquote("a\nb") == "> a\n> b"

    def test_single_line_value_unaffected(self) -> None:
        assert markdown_decoration.blockquote("test") == "> test"
