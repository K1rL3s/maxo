"""Сборка блока импортов. Порядок и группировку потом наводит ruff."""

from collections.abc import Iterable

from unihttp_openapi_generator.ir.types import Import
from unihttp_openapi_generator.render.imports import render_import_lines


def render(items: Iterable[Import]) -> str:
    return render_import_lines(items)
