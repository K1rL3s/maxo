from dataclasses import dataclass
from string import Formatter

from yarl import URL

from maxo.transport.webhook.route.errors import (
    InvalidPathTemplateError,
    InvalidRoutePathError,
    RouteBuildInvalidPathTemplateError,
    RouteBuildMissingParamError,
)


@dataclass(frozen=True, slots=True)
class PathTemplate:
    value: str
    param_names: tuple[str, ...]

    @classmethod
    def from_input(cls, path: str | URL) -> "PathTemplate":
        normalized_path = normalize_path(path)
        return cls(
            value=normalized_path,
            param_names=extract_path_param_names(normalized_path),
        )

    def build(self, params: dict[str, str]) -> str:
        try:
            return self.value.format_map(params)
        except KeyError as exc:
            raise RouteBuildMissingParamError(
                path=self.value,
                param=str(exc.args[0]),
            ) from exc
        except ValueError as exc:
            raise RouteBuildInvalidPathTemplateError(path=self.value) from exc


def normalize_path(path: str | URL) -> str:
    url = path if isinstance(path, URL) else URL(path)

    if url.is_absolute():
        raise InvalidRoutePathError(path=url, reason="path must be relative")
    if url.query_string:
        raise InvalidRoutePathError(
            path=url,
            reason="path must not contain query params; move them to Route(query=...)",
        )
    if url.fragment:
        raise InvalidRoutePathError(
            path=url,
            reason="URL fragment is not supported for route",
        )

    route_path = url.path or "/"
    if not route_path.startswith("/"):
        route_path = f"/{route_path}"

    return route_path


def extract_path_param_names(path_template: str) -> tuple[str, ...]:
    names: list[str] = []

    try:
        parsed = Formatter().parse(path_template)
    except ValueError as exc:
        raise InvalidPathTemplateError(
            path=path_template,
            reason="malformed path template",
        ) from exc

    for _, field_name, format_spec, conversion in parsed:
        if field_name is None:
            continue

        if not field_name:
            raise InvalidPathTemplateError(
                path=path_template,
                reason="empty path param name is not supported",
                value="{}",
            )
        if format_spec:
            raise InvalidPathTemplateError(
                path=path_template,
                reason="path param converters are not supported; use '{name}' only",
                value=f"{{{field_name}:{format_spec}}}",
            )
        if conversion:
            raise InvalidPathTemplateError(
                path=path_template,
                reason="path param conversions are not supported; use '{name}' only",
                value=f"{{{field_name}!{conversion}}}",
            )
        if not field_name.isidentifier():
            raise InvalidPathTemplateError(
                path=path_template,
                reason="path param name must be a valid Python identifier",
                value=field_name,
            )

        names.append(field_name)

    return tuple(names)
