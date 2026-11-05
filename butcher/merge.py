"""
Слияние двух публикаций спеки MAX Bot API в самый полный вариант.

MAX выкладывает контракт дважды: `max-swagger.json` - то, что отдаёт
`dev.max.ru` (русские описания, алиасы развёрнуты в примитивы), и
`max-swagger.yaml` - исходник из репозитория `max-messenger/api-schema`
(английские описания, `nullable`, `deprecated`, иногда поля и параметры,
которых на сайте ещё нет).

База - json: из него идут описания, `required` и ручные правки докстрингов.
Из yaml добираются только те сведения, которых в базе нет: новые пути, методы,
схемы, свойства, параметры и члены enum'ов, а ещё флаги `nullable` и
`deprecated`. Части `allOf` сопоставляются по порядку, и только когда их
одинаковое число: иначе базовая схема остаётся как есть.
"""

from typing import Any

FLAG_KEYS = ("nullable", "deprecated")
OPERATION_DEPTH = 3


def merge_specs(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = _merge(base, extra, ())
    if not isinstance(merged, dict):
        raise TypeError("Спека должна быть объектом")
    return merged


def _merge(base: object, extra: object, path: tuple[str, ...]) -> object:
    if isinstance(base, dict) and isinstance(extra, dict):
        return _merge_mapping(base, extra, path)
    if (
        path
        and path[-1] == "parameters"
        and isinstance(base, list)
        and isinstance(extra, list)
    ):
        return _merge_parameters(base, extra, path)
    if (
        path
        and path[-1] == "allOf"
        and isinstance(base, list)
        and isinstance(extra, list)
        and len(base) == len(extra)
    ):
        return [
            _merge(item, other, path) for item, other in zip(base, extra, strict=True)
        ]
    return base


def _merge_mapping(
    base: dict[str, Any],
    extra: dict[str, Any],
    path: tuple[str, ...],
) -> dict[str, Any]:
    merged = {
        key: _merge(value, extra[key], (*path, key)) if key in extra else value
        for key, value in base.items()
    }
    if _extendable(path):
        merged.update(
            {key: value for key, value in extra.items() if key not in base},
        )
    for flag in FLAG_KEYS:
        if extra.get(flag) and flag not in base:
            merged[flag] = extra[flag]
    if isinstance(base.get("enum"), list) and isinstance(extra.get("enum"), list):
        merged["enum"] = base["enum"] + [
            member for member in extra["enum"] if member not in base["enum"]
        ]
    return merged


def _merge_parameters(
    base: list[Any],
    extra: list[Any],
    path: tuple[str, ...],
) -> list[Any]:
    extra_by_key = {
        key: item for item in extra if (key := _parameter_key(item)) is not None
    }
    merged = [
        (
            _merge(item, extra_by_key[key], path)
            if (key := _parameter_key(item)) in extra_by_key
            else item
        )
        for item in base
    ]
    known = {_parameter_key(item) for item in base}
    merged.extend(item for key, item in extra_by_key.items() if key not in known)
    return merged


def _extendable(path: tuple[str, ...]) -> bool:
    if path[:1] == ("paths",) and len(path) <= OPERATION_DEPTH:
        return True
    if path == ("components", "schemas"):
        return True
    return bool(path) and path[-1] == "properties"


def _parameter_key(item: object) -> tuple[str, str] | None:
    if isinstance(item, dict) and "name" in item:
        return item["name"], item.get("in", "")
    return None
