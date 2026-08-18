"""Запись сгенерированных модулей в дерево `src/maxo`."""

from pathlib import Path

from unihttp_openapi_generator.postprocess import format_path

from butcher import overrides
from butcher.profile import MaxoDocument
from butcher.render import enums, inits, methods, types, unions


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def write(document: MaxoDocument, output_dir: Path) -> list[Path]:
    """Записать типы, enum'ы, union-файлы и методы. Возвращает список файлов."""
    types_dir = output_dir / "types"
    enums_dir = output_dir / "enums"
    methods_dir = output_dir / "bot" / "methods"
    written: list[Path] = []

    for model in document.models:
        path = types_dir / f"{model.module_stem}.py"
        _write(path, types.render(model))
        written.append(path)

    for union_file in document.unions:
        path = types_dir / f"{union_file.module}.py"
        _write(path, unions.render(union_file))
        written.append(path)

    for enum in document.enums:
        path = enums_dir / f"{enum.module_stem}.py"
        _write(path, enums.render(enum))
        written.append(path)

    for method in document.methods:
        path = methods_dir / method.tag / f"{method.module_stem}.py"
        _write(path, methods.render(method))
        written.append(path)

    for tag in {method.tag for method in document.methods}:
        (methods_dir / tag / "__init__.py").touch()

    types_init = types_dir / "__init__.py"
    _write(types_init, inits.types(document, overrides.TYPES_EXTRA_EXPORTS))
    written.append(types_init)

    enums_init = enums_dir / "__init__.py"
    _write(enums_init, inits.enums(document))
    written.append(enums_init)

    methods_init = methods_dir / "__init__.py"
    _write(methods_init, inits.methods(document, overrides.METHODS_EXTRA_EXPORTS))
    written.append(methods_init)

    format_path(output_dir, config_path=Path(__file__).parents[1] / "pyproject.toml")
    return written
