"""Рендер `__init__.py` для `maxo/types`, `maxo/enums` и `maxo/bot/methods`."""

from butcher.overrides import ExtraExport
from butcher.profile import MaxoDocument


def render(exports: list[tuple[str, tuple[str, ...]]]) -> str:
    """Файл реэкспорта: ``from .<module> import <names>`` плюс ``__all__``."""
    lines = sorted(
        f"from .{module} import {', '.join(sorted(names))}"
        for module, names in exports
        if names
    )
    all_names = sorted({name for _, names in exports for name in names})
    rendered = ", ".join(f'"{name}"' for name in all_names)
    comma = "," if rendered else ""
    return "\n".join(lines) + f"\n\n__all__ = ({rendered}{comma})\n"


def types(document: MaxoDocument, extra: tuple[ExtraExport, ...]) -> str:
    exports: list[tuple[str, tuple[str, ...]]] = [
        (model.module_stem, model.exported_names) for model in document.models
    ]
    exports.extend((unions.module, unions.exported_names) for unions in document.unions)
    exports.extend((item.module, item.names) for item in extra)
    return render(exports)


def enums(document: MaxoDocument) -> str:
    return render([(enum.module_stem, enum.exported_names) for enum in document.enums])


def methods(document: MaxoDocument, extra: tuple[ExtraExport, ...]) -> str:
    exports: list[tuple[str, tuple[str, ...]]] = [
        (f"{method.tag}.{method.module_stem}", (method.name,))
        for method in document.methods
    ]
    exports.extend((item.module, item.names) for item in extra)
    return render(exports)
