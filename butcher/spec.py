"""
Чтение OpenAPI-спеки и построение IR через `unihttp-openapi-generator`.

Butcher не разбирает свагер сам: за `allOf`, `oneOf`/`anyOf`, `nullable` в обеих
формах, форматы, дефолты, `readOnly`, дискриминаторы, тела запросов и коллизии
имён отвечает генератор. Здесь только выбор режима, в котором нужен maxo.
"""

from itertools import chain
from typing import Any

from unihttp_openapi_generator.ir.builder import build_ir
from unihttp_openapi_generator.ir.document import IRDocument
from unihttp_openapi_generator.loader import load_spec
from unihttp_openapi_generator.refs import RefResolver

from butcher.merge import merge_specs


def load(spec_source: str, extra_source: str | None = None) -> IRDocument:
    """
    Загрузить спеку и построить IR в том виде, в котором его ждёт maxo.

    Args:
        spec_source: путь или URL спеки (JSON или YAML).
        extra_source: вторая публикация той же спеки, из которой добираются
            сведения, отсутствующие в первой.

    """
    spec = load_spec(spec_source)
    if extra_source is not None:
        spec = merge_specs(spec, load_spec(extra_source))
    resolver = RefResolver(spec, root_uri=spec_source)
    mark_deprecated_parameters(spec, resolver)
    return build_ir(
        spec,
        resolver,
        root_uri=spec_source,
        # Необязательные поля должны остаться `Omittable[...] = Omitted()`,
        # а не схлопнуться в `T | None = None`.
        omit_optionals=True,
        # Базовые классы вместо копирования полей родителя в каждый подтип:
        # `PhotoAttachment(Attachment)`, `MessageCreated(MaxUpdate)`.
        inheritance=True,
    )


DEPRECATED_PARAMETER_NOTE = "_Устаревший параметр_"


def mark_deprecated_parameters(spec: dict[str, Any], resolver: RefResolver) -> None:
    marked: set[int] = set()
    for path_item in spec["paths"].values():
        operations = (op for op in path_item.values() if isinstance(op, dict))
        for raw in chain(
            path_item.get("parameters", ()),
            *(op.get("parameters", ()) for op in operations),
        ):
            parameter = raw
            if "$ref" in raw:
                parameter = resolver.resolve_ref(raw["$ref"]).value
            if not parameter.get("deprecated") or id(parameter) in marked:
                continue
            marked.add(id(parameter))
            description = parameter.get("description")
            parameter["description"] = (
                f"{description}\n\n{DEPRECATED_PARAMETER_NOTE}"
                if description
                else DEPRECATED_PARAMETER_NOTE
            )
