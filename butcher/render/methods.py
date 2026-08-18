"""Рендер файлов `maxo/bot/methods/<tag>/*.py`."""

from butcher.profile import Method
from butcher.render import docs, fields, imports


def render(method: Method) -> str:
    lines = [
        imports.render(method.imports),
        "",
        "",
        f"class {method.name}(MaxoMethod[{method.returns}]):",
    ]

    lines.extend(
        docs.render(
            docs.build_parts(
                summary=method.summary,
                description=method.description,
                parameters=[
                    (item.name, item.description)
                    for item in sorted(method.fields, key=lambda field_: field_.name)
                ],
                source_link=method.doc_link,
            ),
        ),
    )

    lines.extend(
        [
            "",
            f'    __url__ = "{method.url}"',
            f'    __method__ = "{method.http_method}"',
        ],
    )

    for group in method.field_groups:
        lines.append("")
        for item in group:
            lines.extend(fields.render(item))

    return "\n".join(lines) + "\n"
