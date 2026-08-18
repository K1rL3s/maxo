"""Рендер одного поля и парного к нему `unsafe_*`-свойства."""

from butcher.profile import Field
from butcher.render import docs


def render(field: Field, indent: str = "    ", reflow: bool = False) -> list[str]:
    """Строки объявления поля вместе с его docstring'ом."""
    if field.bare_assignment:
        return [f"{indent}{field.name} = {field.default}"]

    annotation = field.annotation
    if field.omittable:
        annotation = f"Omittable[{annotation}]"
    if field.marker is not None:
        annotation = f"{field.marker}[{annotation}]"

    line = f"{indent}{field.name}: {annotation}"
    if field.default is not None:
        line += f" = {field.default}"
    elif field.omittable:
        line += " = Omitted()"
    elif field.optional:
        line += " = None"
    if field.comment is not None:
        line += f"  # {field.comment}"

    return [line, *docs.render_field(field.description, indent, reflow=reflow)]


def render_unsafe(field: Field, indent: str = "    ") -> list[str]:
    """Свойство `unsafe_*`: значение или :class:`AttributeIsEmptyError`."""
    return [
        "",
        f"{indent}@property",
        f"{indent}def unsafe_{field.name}(self) -> {field.bare_annotation}:",
        f"{indent}    if is_defined(self.{field.name}):",
        f"{indent}        return self.{field.name}",
        "",
        f"{indent}    raise AttributeIsEmptyError(",
        f"{indent}        obj=self,",
        f'{indent}        attr="{field.name}",',
        f"{indent}    )",
    ]
