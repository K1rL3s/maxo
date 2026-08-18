"""
Чтение OpenAPI-спеки и построение IR через `unihttp-openapi-generator`.

Butcher не разбирает свагер сам: за `allOf`, `oneOf`/`anyOf`, `nullable` в обеих
формах, форматы, дефолты, `readOnly`, дискриминаторы, тела запросов и коллизии
имён отвечает генератор. Здесь только выбор режима, в котором нужен maxo.
"""

from unihttp_openapi_generator.ir.builder import build_ir
from unihttp_openapi_generator.ir.document import IRDocument
from unihttp_openapi_generator.loader import load_spec
from unihttp_openapi_generator.refs import RefResolver


def load(spec_source: str) -> IRDocument:
    """
    Загрузить спеку и построить IR в том виде, в котором его ждёт maxo.

    Args:
        spec_source: путь или URL спеки (JSON или YAML).

    """
    spec = load_spec(spec_source)
    return build_ir(
        spec,
        RefResolver(spec, root_uri=spec_source),
        root_uri=spec_source,
        # Необязательные поля должны остаться `Omittable[...] = Omitted()`,
        # а не схлопнуться в `T | None = None`.
        omit_optionals=True,
        # Базовые классы вместо копирования полей родителя в каждый подтип:
        # `PhotoAttachment(Attachment)`, `MessageCreated(MaxUpdate)`.
        inheritance=True,
    )
