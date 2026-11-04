from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from butcher.site_spec.markup import BLOCK_TAGS, Element, parse_html

MIN_PAGES = 40
MIN_PARAMS = 1000
METHOD_PAGE_PREFIX = "methods__"
CODES_HEADING = "Коды ответов"
OBJECT_PROPERTIES_HEADING = "Свойства объекта"
SECTION_HEADINGS = frozenset(
    {
        "Авторизация",
        "Параметры",
        "Тело запроса",
        "Результат",
        CODES_HEADING,
        "Пример объекта",
    },
)
SECTION_HEADING_TAGS = ("h2", "h3", "h4")
CODE_ROW_CELLS = 2
REQUEST_PARTS = 2


class SiteFormatError(Exception):
    pass


@dataclass(slots=True)
class Selector:
    param: str
    group: str
    values: list[str]


@dataclass(slots=True)
class Param:
    name: str
    type: str
    optional: bool
    pattern: str | None
    description: str
    selector: Selector | None = None
    children: "list[Param] | None" = None
    variants: "dict[str, list[Param]] | None" = None

    def count(self) -> int:
        nested = list(self.children or [])
        for params in (self.variants or {}).values():
            nested.extend(params)
        return 1 + sum(param.count() for param in nested)


@dataclass(slots=True)
class Section:
    heading: str | None
    params: list[Param]


@dataclass(slots=True)
class ResponseCode:
    code: str
    description: str


@dataclass(slots=True)
class Page:
    key: str
    title: str = ""
    method: str | None = None
    path: str | None = None
    intro: str = ""
    sections: list[Section] = field(default_factory=list)
    codes: list[ResponseCode] = field(default_factory=list)

    def count_params(self) -> int:
        return sum(
            param.count() for section in self.sections for param in section.params
        )


def parse_page(key: str, text: str) -> Page:
    main = parse_html(text).find(lambda element: element.tag == "main")
    if main is None:
        raise SiteFormatError(f"{key}: на странице нет <main>")
    page = Page(key)
    stage = "head"
    heading: str | None = None
    intro: list[Element | str] = []
    for child in _flatten_paragraphs(main):
        if isinstance(child, str):
            if stage == "intro":
                intro.append(child)
            continue
        if child.tag == "h1":
            page.title = child.text().strip()
            stage = "intro"
            continue
        if child.has_class("md-source-link") or (
            _is_accent(child) and stage == "intro" and not page.method and not intro
        ):
            continue
        if child.has_class("request"):
            spans = child.elements()
            if len(spans) < REQUEST_PARTS:
                raise SiteFormatError(f"{key}: строка запроса без метода или пути")
            page.method = spans[0].text().strip()
            page.path = spans[1].text().strip()
            intro = []
            continue
        if child.tag in SECTION_HEADING_TAGS and child.has_class("linked-heading"):
            title = (child.find_class("linked-heading__text") or child).text().strip()
            if child.tag == "h2" and _is_section_heading(title):
                if title.startswith(OBJECT_PROPERTIES_HEADING) and stage == "intro":
                    intro.append(child)
                stage = "sections"
                heading = title
            elif stage == "intro":
                intro.append(child)
            elif stage == "sections" and child.tag == "h2":
                raise SiteFormatError(f"{key}: неизвестный раздел {title!r}")
            continue
        if child.has_class("api-params"):
            stage = "sections"
            page.sections.append(Section(heading, _parse_params(key, child)))
            continue
        if stage == "sections" and heading == CODES_HEADING:
            page.codes.extend(_parse_codes(child))
            continue
        if stage == "intro":
            intro.append(child)
    if key.startswith(METHOD_PAGE_PREFIX) and not page.method:
        raise SiteFormatError(f"{key}: у страницы метода нет строки запроса")
    wrapper = Element("div", {}, None)
    wrapper.children = [node for node in intro if not _is_site_banner(node)]
    page.intro = wrapper.markdown()
    return page


def parse_pages(
    pages_dir: Path,
    *,
    min_pages: int = MIN_PAGES,
    min_params: int = MIN_PARAMS,
) -> list[Page]:
    pages = [
        parse_page(path.stem, path.read_text(encoding="utf-8"))
        for path in sorted(pages_dir.glob("*.html"))
    ]
    if len(pages) < min_pages:
        raise SiteFormatError(
            f"Страниц {len(pages)} в {pages_dir}, ожидалось не меньше {min_pages}",
        )
    params = sum(page.count_params() for page in pages)
    if params < min_params:
        raise SiteFormatError(
            f"Параметров на страницах {params}, ожидалось не меньше {min_params}: "
            "разметка сайта изменилась",
        )
    return pages


def _parse_params(key: str, container: Element) -> list[Param]:
    params: list[Param] = []
    for child in container.elements():
        if child.has_class("api-param"):
            params.append(_parse_param(key, child))
        elif child.has_class("api-param-children"):
            if not params:
                raise SiteFormatError(f"{key}: вложенные параметры без родителя")
            params[-1].children = _parse_params(key, child)
        elif child.has_class("api-param-variant"):
            owner = _variant_owner(key, params, child.attrs.get("data-param"))
            if owner.variants is None:
                owner.variants = {}
            owner.variants[child.attrs.get("data-variant", "")] = _parse_params(
                key,
                child,
            )
        elif child.tag == "p":
            params.extend(_parse_params(key, child))
    return params


def _parse_param(key: str, element: Element) -> Param:
    name = element.find_class("api-param__name")
    if name is None:
        raise SiteFormatError(f"{key}: параметр без имени")
    type_ = element.find_class("api-param__type")
    pattern = element.find_class("api-param__pattern")
    description = element.find_class("api-param__desc")
    param = Param(
        name=name.own_text().strip(),
        type=" ".join(type_.text().split()) if type_ is not None else "",
        optional=element.find_class("api-param__optional") is not None,
        pattern=pattern.text().strip() if pattern is not None else None,
        description="",
    )
    if description is None:
        return param
    selector = description.find_class("api-param__enum")
    if selector is not None:
        param.selector = Selector(
            param=selector.attrs.get("data-param", ""),
            group=selector.attrs.get("data-group", ""),
            values=[
                option.text().strip()
                for option in selector.iter_class("api-param__enum-option")
            ],
        )
        if selector.parent is not None:
            selector.parent.children.remove(selector)
    param.description = description.markdown()
    return param


def _variant_owner(key: str, params: list[Param], selector: str | None) -> Param:
    for param in reversed(params):
        if param.selector is not None and param.selector.param == selector:
            return param
    raise SiteFormatError(f"{key}: вариант {selector!r} без селектора")


def _parse_codes(element: Element) -> Iterator[ResponseCode]:
    for row in element.iter_tag("tr"):
        cells = [cell for cell in row.elements() if cell.tag == "td"]
        if len(cells) == CODE_ROW_CELLS:
            yield ResponseCode(cells[0].text().strip(), cells[1].markdown())


def _flatten_paragraphs(element: Element) -> Iterator[Element | str]:
    for child in element.children:
        if (
            isinstance(child, Element)
            and child.tag == "p"
            and any(
                isinstance(node, Element)
                and (node.tag in BLOCK_TAGS or node.has_class("code-card"))
                for node in child.children
            )
        ):
            yield from _flatten_paragraphs(child)
        else:
            yield child


def _is_section_heading(title: str) -> bool:
    return title in SECTION_HEADINGS or title.startswith(OBJECT_PROPERTIES_HEADING)


def _is_accent(element: Element) -> bool:
    return element.tag == "blockquote" and element.has_class("accent")


def _is_site_banner(node: Element | str) -> bool:
    if isinstance(node, str) or not _is_accent(node):
        return False
    text = node.text()
    return "platform-api2.max.ru" in text and "Минцифры" in text
