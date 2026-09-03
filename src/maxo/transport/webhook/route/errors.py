import logging
from collections.abc import Iterable
from dataclasses import field

from yarl import URL

from maxo.transport.webhook.errors import MaxoWebhookError


def format_names(names: Iterable[str]) -> str:
    return ", ".join(repr(name) for name in sorted(names))


class RouteError(MaxoWebhookError):
    code = "route_error"


class RouteConfigError(RouteError):
    status_code = 500
    public_detail = "Internal server error"
    log_level = logging.ERROR

    # kw_only, чтобы subclass-ы могли добавлять свои обязательные поля
    # после этого (у него есть значение по умолчанию).
    message: str = field(default="", kw_only=True)

    def __str__(self) -> str:
        return self.message


class RouteBuildError(RouteError):
    status_code = 500
    public_detail = "Internal server error"
    log_level = logging.ERROR


class RouteMatchError(RouteError):
    status_code = 404
    public_detail = "Not found"
    log_level = logging.INFO


class InvalidBaseUrlError(RouteConfigError):
    code = "route_config_invalid_base_url"

    base_url: URL = field(kw_only=True)
    reason: str = field(kw_only=True)

    def __str__(self) -> str:
        return (
            f"Invalid Route base_url. Reason: {self.reason}. base_url={self.base_url}."
        )


class InvalidRoutePathError(RouteConfigError):
    code = "route_config_invalid_path"

    path: URL = field(kw_only=True)
    reason: str = field(kw_only=True)

    def __str__(self) -> str:
        return f"Invalid Route path. Reason: {self.reason}. path={self.path!r}."


class InvalidPathTemplateError(RouteConfigError):
    code = "route_config_invalid_path_template"

    path: str = field(kw_only=True)
    reason: str = field(kw_only=True)
    value: str | None = field(default=None, kw_only=True)

    def __str__(self) -> str:
        message = (
            f"Invalid Route path template. Reason: {self.reason}. path={self.path!r}."
        )

        if self.value is not None:
            message += f" Value: {self.value!r}."

        return message


class RepeatedPathParamError(RouteConfigError):
    code = "route_config_repeated_path_params"

    path: str = field(kw_only=True)
    repeated_params: Iterable[str] = field(kw_only=True)

    def __post_init__(self) -> None:
        self.repeated_params = tuple(sorted(self.repeated_params))

    def __str__(self) -> str:
        return (
            "Invalid Route config: repeated path params are not supported. "
            f"path={self.path!r}. "
            f"Repeated params: {format_names(self.repeated_params)}."
        )


class MissingRouteParamDeclarationError(RouteConfigError):
    code = "route_config_missing_param_declarations"

    path: str = field(kw_only=True)
    missing_params: Iterable[str] = field(kw_only=True)

    def __post_init__(self) -> None:
        self.missing_params = tuple(sorted(self.missing_params))

    def __str__(self) -> str:
        return (
            "Invalid Route config: some path params are not declared in "
            f"Route(params=...). path={self.path!r}. "
            f"Missing declarations: {format_names(self.missing_params)}."
        )


class UnusedRouteParamDeclarationError(RouteConfigError):
    code = "route_config_unused_param_declarations"

    path: str = field(kw_only=True)
    unused_params: Iterable[str] = field(kw_only=True)

    def __post_init__(self) -> None:
        self.unused_params = tuple(sorted(self.unused_params))

    def __str__(self) -> str:
        return (
            "Invalid Route config: some Route(params=...) declarations are not "
            f"used in path. path={self.path!r}. "
            f"Unused declarations: {format_names(self.unused_params)}."
        )


class UnknownQueryParamReferenceError(RouteConfigError):
    code = "route_config_unknown_query_param_refs"

    path: str = field(kw_only=True)
    unknown_params: Iterable[str] = field(kw_only=True)

    def __post_init__(self) -> None:
        self.unknown_params = tuple(sorted(self.unknown_params))

    def __str__(self) -> str:
        return (
            "Invalid Route config: query references params that are not "
            f"declared in path. path={self.path!r}. "
            f"Unknown params: {format_names(self.unknown_params)}."
        )


class RouteBuildMissingParamError(RouteBuildError):
    code = "route_build_missing_param"

    path: str
    param: str

    def __str__(self) -> str:
        return (
            f"Failed to build URL: missing route param. "
            f"path={self.path!r}. param={self.param!r}."
        )


class RouteBuildInvalidPathTemplateError(RouteBuildError):
    code = "route_build_invalid_path_template"

    path: str

    def __str__(self) -> str:
        return f"Failed to build URL: invalid path template. path={self.path!r}."


class MissingPathParamError(RouteMatchError):
    code = "route_match_missing_path_param"

    param: str
    available_params: Iterable[str]

    def __post_init__(self) -> None:
        self.available_params = tuple(sorted(self.available_params))

    def __str__(self) -> str:
        return (
            "Incoming request does not match route: missing path param. "
            f"param={self.param!r}. "
            f"Available path params: {format_names(self.available_params)}."
        )


class InvalidPathParamError(RouteMatchError):
    code = "route_match_invalid_path_param"

    param: str
    value: str

    def __str__(self) -> str:
        return (
            "Incoming request does not match route: path param value is invalid. "
            f"param={self.param!r}. value={self.value!r}."
        )


class MissingQueryParamError(RouteMatchError):
    code = "route_match_missing_query_param"

    query_param: str
    available_query_params: Iterable[str]

    def __post_init__(self) -> None:
        self.available_query_params = tuple(sorted(self.available_query_params))

    def __str__(self) -> str:
        return (
            "Incoming request does not match route: missing query param. "
            f"query_param={self.query_param!r}. "
            f"Available query params: {format_names(self.available_query_params)}."
        )


class QueryParamMismatchError(RouteMatchError):
    code = "route_match_query_param_mismatch"

    query_param: str
    expected: Iterable[str]
    got: Iterable[str]

    def __post_init__(self) -> None:
        self.expected = tuple(self.expected)
        self.got = tuple(self.got)

    def __str__(self) -> str:
        return (
            "Incoming request does not match route: query param values mismatch. "
            f"query_param={self.query_param!r}. "
            f"Expected values: {self.expected!r}. "
            f"Got values: {self.got!r}."
        )


class UnexpectedQueryParamError(RouteMatchError):
    code = "route_match_unexpected_query_param"

    query_params: Iterable[str]
    expected_query_params: Iterable[str]

    def __post_init__(self) -> None:
        self.query_params = tuple(sorted(self.query_params))
        self.expected_query_params = tuple(sorted(self.expected_query_params))

    def __str__(self) -> str:
        return (
            "Incoming request does not match route: unexpected query params. "
            f"Unexpected query params: {format_names(self.query_params)}. "
            f"Expected query params: {format_names(self.expected_query_params)}."
        )
