from pathlib import Path

import pytest

from butcher.site_spec.pages import SiteFormatError, parse_page, parse_pages

PAGES_DIR = Path(__file__).parent / "site_pages"

HEADING = (
    '<h2 class="linked-heading"><span class="linked-heading__text">'
    "<span>{}</span></span></h2>"
)
PARAM = (
    '<div class="api-param"><div class="api-param__row"><div class="api-param__left">'
    '<span class="api-param__name">{name}</span><div class="api-param__meta">'
    '<span class="api-param__type">{type}</span></div></div>'
    '<div class="api-param__desc">{desc}</div></div></div>'
)
SELECTOR = (
    '<div class="api-param"><div class="api-param__row"><div class="api-param__left">'
    '<span class="api-param__name">type</span><div class="api-param__meta">'
    '<span class="api-param__type">string</span></div></div>'
    '<div class="api-param__desc"><div class="api-param__enum" data-param="type" '
    'data-group="AttachmentRequest"><div class="api-param__enum-list" hidden>'
    '<div class="api-param__enum-option">image</div>'
    '<div class="api-param__enum-option">location</div></div></div>'
    "Тип вложения</div></div></div>"
)


def page_html(*parts: str, request: str = "") -> str:
    return (
        '<html><body><main><h1 id="page-title">Тест</h1>'
        f"{request}<p>Описание</p>{''.join(parts)}</main></body></html>"
    )


def read(name: str) -> str:
    return (PAGES_DIR / f"{name}.html").read_text(encoding="utf-8")


def test_object_page():
    page = parse_page("objects__User", read("objects__User"))

    assert (page.title, page.method, page.path) == ("User", None, None)
    assert page.intro.startswith("Объект, описывающий один из вариантов наследования")
    assert "- [`UserWithPhoto`](/docs-api/objects/UserWithPhoto) - объект" in page.intro
    [section] = page.sections
    assert section.heading is None
    assert [param.name for param in section.params] == [
        "user_id",
        "first_name",
        "last_name",
        "username",
        "is_bot",
        "last_activity_time",
        "name",
    ]
    last_name = section.params[2]
    assert (last_name.type, last_name.optional) == ("string Nullable", True)
    assert section.params[0].type == "integer <int64>"
    assert section.params[4].description == "`true`, если это бот"


def test_method_page():
    page = parse_page(
        "methods__POST__chats__-chatId-__members",
        read("methods__POST__chats__-chatId-__members"),
    )

    assert (page.method, page.path) == ("POST", "/chats/{chatId}/members")
    assert page.title == "Добавление участников в групповой чат"
    assert page.intro.startswith("Добавляет участников в групповой чат")
    assert [section.heading for section in page.sections] == [
        "Авторизация",
        "Параметры",
        "Тело запроса",
        "Результат",
    ]
    [user_ids] = page.sections[2].params
    assert user_ids.name == "user_ids"
    assert not user_ids.optional
    assert [code.code for code in page.codes] == ["200", "401", "403", "404", "500"]


def test_method_page_pattern_and_codes():
    page = parse_page(
        "methods__DELETE__chats__-chatId-__pin",
        read("methods__DELETE__chats__-chatId-__pin"),
    )

    [chat_id] = page.sections[1].params
    assert chat_id.pattern is not None
    assert page.codes[0].description


def test_variants_and_children():
    html = page_html(
        '<div class="api-params">',
        SELECTOR,
        '<div class="api-param-variant" data-param="type" data-variant="image" '
        'data-group="AttachmentRequest">',
        PARAM.format(name="payload", type="object Payload", desc="Данные"),
        '<div class="api-param-children">',
        PARAM.format(name="url", type="string", desc="URL"),
        "</div></div>",
        '<div class="api-param-variant" data-param="type" data-variant="location" '
        'data-group="AttachmentRequest">',
        PARAM.format(name="latitude", type="number <double>", desc="Широта"),
        "</div></div>",
    )

    [section] = parse_page("objects__Test", html).sections
    [selector] = section.params
    assert selector.selector is not None
    assert selector.selector.values == ["image", "location"]
    assert selector.selector.group == "AttachmentRequest"
    assert selector.description == "Тип вложения"
    assert selector.variants is not None
    assert list(selector.variants) == ["image", "location"]
    [payload] = selector.variants["image"]
    assert payload.children is not None
    assert [child.name for child in payload.children] == ["url"]
    assert selector.count() == 4


def test_intro_heading_before_sections():
    html = page_html(
        HEADING.format("Доступные права администратора"),
        "<ul><li>read</li></ul>",
        HEADING.format("Параметры"),
        '<div class="api-params">',
        PARAM.format(name="chatId", type="integer <int64>", desc="ID"),
        "</div>",
        request='<p class="request"><span>POST</span><code>/chats</code></p>',
    )

    page = parse_page("methods__POST__chats", html)

    assert "## Доступные права администратора" in page.intro
    assert [section.heading for section in page.sections] == ["Параметры"]


def test_unknown_section_heading():
    html = page_html(
        HEADING.format("Параметры"),
        '<div class="api-params"></div>',
        HEADING.format("Ограничения"),
    )

    with pytest.raises(SiteFormatError, match="Ограничения"):
        parse_page("objects__Test", html)


def test_method_page_without_request_line():
    with pytest.raises(SiteFormatError, match="строки запроса"):
        parse_page("methods__GET__me", page_html())


def test_page_without_main():
    with pytest.raises(SiteFormatError, match="<main>"):
        parse_page("objects__User", "<html><body></body></html>")


def test_variant_without_selector():
    html = page_html(
        '<div class="api-params"><div class="api-param-variant" data-param="type" '
        'data-variant="image"></div></div>',
    )

    with pytest.raises(SiteFormatError, match="без селектора"):
        parse_page("objects__Test", html)


def test_parse_pages():
    pages = parse_pages(PAGES_DIR, min_pages=3, min_params=10)

    assert [page.key for page in pages] == [
        "methods__DELETE__chats__-chatId-__pin",
        "methods__POST__chats__-chatId-__members",
        "objects__User",
    ]


def test_parse_pages_too_few_pages():
    with pytest.raises(SiteFormatError, match="Страниц 3"):
        parse_pages(PAGES_DIR)


def test_parse_pages_too_few_params():
    with pytest.raises(SiteFormatError, match="разметка сайта изменилась"):
        parse_pages(PAGES_DIR, min_pages=3, min_params=1000)
