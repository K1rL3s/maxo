import copy
from typing import Any

from butcher.site_spec.overlay import (
    ReportEntry,
    build_site_spec,
    parse_type,
    plain,
    split_description,
)
from butcher.site_spec.pages import Page, Param, ResponseCode, Section, Selector

PAGE = "methods__POST__things__-thingId-"

BASE: dict[str, Any] = {
    "paths": {
        "/things/{thingId}": {
            "post": {
                "summary": "Создание вещи",
                "description": "Создаёт вещь",
                "parameters": [
                    {
                        "name": "thingId",
                        "in": "path",
                        "required": True,
                        "description": "ID вещи",
                        "schema": {"type": "integer", "format": "int64"},
                    },
                    {
                        "name": "legacy",
                        "in": "query",
                        "description": "Старый параметр",
                        "schema": {"type": "boolean"},
                    },
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Thing"},
                        },
                    },
                },
                "responses": {
                    "200": {
                        "description": "Ок",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Result"},
                            },
                        },
                    },
                },
            },
        },
        "/hidden": {"get": {"summary": "Скрытый", "responses": {}}},
    },
    "components": {
        "schemas": {
            "Thing": {
                "description": "Вещь",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "description": "Имя"},
                    "color": {
                        "type": "string",
                        "enum": ["red", "blue"],
                        "description": "Цвет",
                    },
                    "note": {
                        "type": "string",
                        "nullable": True,
                        "description": "Заметка",
                    },
                    "size": {"type": "integer", "description": "Размер"},
                    "manual": {"type": "string", "description": "Ручное поле"},
                },
            },
            "Result": {
                "properties": {"success": {"type": "boolean", "description": "Успех"}},
            },
        },
    },
}


def param(name: str, type_: str, description: str, *, optional: bool = True):
    return Param(
        name=name,
        type=type_,
        optional=optional,
        pattern=None,
        description=description,
    )


def method_page() -> Page:
    return Page(
        key=PAGE,
        title="Создание вещи",
        method="POST",
        path="/things/{thingId}",
        intro="Создаёт вещь",
        sections=[
            Section(
                "Параметры",
                [
                    param("thingId", "integer <int64>", "ID вещи", optional=False),
                    param("fresh", "boolean", "Новый параметр"),
                ],
            ),
            Section(
                "Тело запроса",
                [
                    param("name", "string", "Новое **имя**"),
                    param(
                        "color",
                        "enum",
                        'Возможные значения в enum: `"red"` `"green"`\nЦвет',
                    ),
                    param("note", "string", "Заметка"),
                    param("size", "string", "Размер"),
                    param(
                        "weight",
                        "number <double>",
                        "до `10` символов\nВес",
                        optional=False,
                    ),
                ],
            ),
            Section("Результат", [param("success", "boolean", "Успех")]),
        ],
        codes=[ResponseCode("200", "Ок"), ResponseCode("404", "Не найдено")],
    )


def object_page(title: str, intro: str) -> Page:
    return Page(key=f"objects__{title}", title=title, intro=intro)


def build(*pages: Page):
    base = copy.deepcopy(BASE)
    spec, report = build_site_spec(base, list(pages))
    assert base == BASE
    return spec, report


def entries(report: list[ReportEntry], kind: str) -> set[tuple[str, str]]:
    return {(entry.location, entry.fact) for entry in report if entry.kind == kind}


def test_changes_applied():
    spec, report = build(method_page())

    thing = spec["components"]["schemas"]["Thing"]
    assert thing["properties"]["name"]["description"] == "Новое **имя**"
    assert "name" not in thing["required"]
    assert thing["properties"]["color"]["enum"] == ["red", "green"]
    assert "nullable" not in thing["properties"]["note"]
    assert entries(report, "changed") == {
        ("Thing/properties/name", "description"),
        ("Thing/properties/name", "required"),
        ("Thing/properties/color", "enum"),
        ("Thing/properties/note", "nullable"),
    }


def test_type_change_is_manual():
    spec, report = build(method_page())

    assert spec["components"]["schemas"]["Thing"]["properties"]["size"] == {
        "type": "integer",
        "description": "Размер",
    }
    assert entries(report, "manual") == {("Thing/properties/size", "type")}


def test_additions():
    spec, report = build(method_page())

    thing = spec["components"]["schemas"]["Thing"]
    assert thing["properties"]["weight"] == {
        "type": "number",
        "format": "double",
        "description": "Вес",
        "maxLength": 10,
    }
    assert "weight" in thing["required"]
    operation = spec["paths"]["/things/{thingId}"]["post"]
    assert operation["parameters"][-1] == {
        "name": "fresh",
        "in": "query",
        "required": False,
        "description": "Новый параметр",
        "schema": {"type": "boolean"},
    }
    assert operation["responses"]["404"] == {"description": "Не найдено"}
    assert entries(report, "added") == {
        ("Thing/properties/weight", "number <double>"),
        ("POST /things/{thingId} parameters/fresh", ""),
        ("POST /things/{thingId} responses/404", ""),
    }


def test_removals_only_reported():
    spec, report = build(method_page())

    assert "manual" in spec["components"]["schemas"]["Thing"]["properties"]
    assert "/hidden" in spec["paths"]
    names = [
        item["name"]
        for item in spec["paths"]["/things/{thingId}"]["post"]["parameters"]
    ]
    assert "legacy" in names
    assert entries(report, "removed") == {
        ("Thing/properties/manual", ""),
        ("POST /things/{thingId} parameters/legacy", ""),
        ("GET /hidden", ""),
    }
    [removed] = [
        entry for entry in report if entry.location == "Thing/properties/manual"
    ]
    assert removed.pages == (PAGE,)


def test_object_page_description():
    spec, report = build(method_page(), object_page("Thing", "Вещь с **сайта**"))

    assert spec["components"]["schemas"]["Thing"]["description"] == "Вещь с **сайта**"
    assert ("Thing", "description") in entries(report, "changed")


def test_unknown_object_page():
    _, report = build(method_page(), object_page("Ghost", "Призрак"))

    assert ("Ghost", "schema") in entries(report, "manual")


def test_unchanged_site_reports_nothing_applied():
    page = method_page()
    page.sections = [page.sections[0], page.sections[2]]
    page.sections[0].params.pop()
    page.codes.pop()
    spec, report = build(page)

    assert spec == BASE
    assert {entry.kind for entry in report} == {"removed"}


def test_description_conflict():
    first = method_page()
    second = method_page()
    second.key = "objects__Thing"
    second.title = "Thing"
    second.method = second.path = None
    second.sections = [Section(None, [param("name", "string", "Другое имя")])]
    _, report = build(first, second)

    [conflict] = [entry for entry in report if entry.kind == "conflict"]
    assert (conflict.location, conflict.fact) == (
        "Thing/properties/name",
        "description",
    )


def test_parse_type():
    nullable = parse_type("integer <int64> Nullable")
    assert (nullable.base, nullable.format, nullable.nullable) == (
        "integer",
        "int64",
        True,
    )
    matrix = parse_type("Button[][]")
    assert (matrix.array, matrix.name) == (2, "Button")
    strings = parse_type("array <string>")
    assert (strings.array, strings.item_base, strings.format) == (1, "string", None)
    ranged = parse_type("integer [1-100]")
    assert (ranged.minimum, ranged.maximum) == (1, 100)
    assert parse_type("object VideoThumbnail Nullable").name == "VideoThumbnail"


def test_split_description():
    assert split_description("до `16000` символов\nОписание") == (
        {"maxLength": 16000},
        "Описание",
    )
    facts, rest = split_description(
        "от `1` до `64` символов\n\nПо умолчанию: `50`\n\nТекст",
    )
    assert facts == {"minLength": 1, "maxLength": 64, "default": "50"}
    assert rest == "Текст"
    assert split_description('Возможные значения в enum: `"chat"` `"dialog"`\nТип')[
        0
    ] == {
        "enum": ["chat", "dialog"],
    }


def test_plain():
    assert plain("**Обратите внимание**:<br/>- Все [тут](/x#a%20b)") == plain(
        "Обратите внимание: Все тут",
    )
    assert plain(None) == ""
    assert plain("ID\u00a0чата ,\u00a0канала.") == "ID чата, канала"


def test_conflict_applies_most_common_text():
    pages = [method_page() for _ in range(3)]
    for key, page in zip("abc", pages, strict=True):
        page.key = f"methods__{key}"
    pages[0].sections[1].params[0].description = "Старое имя"
    pages[1].sections[1].params[0].description = "Новое **имя**"
    pages[2].sections[1].params[0].description = "Новое **имя**"
    spec, report = build(*pages)

    name = spec["components"]["schemas"]["Thing"]["properties"]["name"]
    assert name["description"] == "Новое **имя**"
    assert ("Thing/properties/name", "description") in entries(report, "conflict")


def test_added_schemas_keep_pages():
    base = copy.deepcopy(BASE)
    schemas = base["components"]["schemas"]
    schemas["Shape"] = {
        "discriminator": {"propertyName": "kind", "mapping": {}},
        "properties": {"kind": {"type": "string", "description": "Вид"}},
    }
    schemas["Thing"]["properties"]["shape"] = {"$ref": "#/components/schemas/Shape"}
    kind = param("kind", "string", "Вид")
    kind.selector = Selector("kind", "Shape", ["circle"])
    kind.variants = {"circle": [param("radius", "number", "Радиус")]}
    shape = param("shape", "object Shape", "")
    shape.children = [kind]
    brand = param("brand", "object Brand", "Бренд")
    brand.children = [param("title", "string", "Название")]
    pages = [method_page(), method_page()]
    pages[1].key = "methods__POST__copy"
    for page in pages:
        page.sections[1].params += [shape, brand]
    spec, report = build_site_spec(base, pages)

    assert "CircleShape" in spec["components"]["schemas"]
    added = {entry.location: entry.pages for entry in report if entry.kind == "added"}
    assert added["Brand"] == ("methods__POST__copy", PAGE)
    assert added["CircleShape"] == ("methods__POST__copy", PAGE)


def test_new_variant_keeps_existing_schema():
    base = copy.deepcopy(BASE)
    schemas = base["components"]["schemas"]
    schemas["Shape"] = {
        "discriminator": {"propertyName": "kind", "mapping": {}},
        "properties": {"kind": {"type": "string", "description": "Вид"}},
    }
    schemas["CircleShape"] = {"properties": {"radius": {"type": "integer"}}}
    schemas["Thing"]["properties"]["kind"] = {"$ref": "#/components/schemas/Shape"}
    kind = param("kind", "object Shape", "")
    kind.children = [param("kind", "string", "Вид")]
    kind.children[0].selector = Selector("kind", "Shape", ["circle"])
    kind.children[0].variants = {"circle": [param("radius", "number", "Радиус")]}
    page = method_page()
    page.sections[1].params.append(kind)
    expected = copy.deepcopy(schemas["CircleShape"])
    spec, report = build_site_spec(base, [page])

    assert spec["components"]["schemas"]["CircleShape"] == expected
    assert spec["components"]["schemas"]["Shape"]["discriminator"]["mapping"] == {}
    assert ("CircleShape", "Shape[circle]") in entries(report, "manual")
