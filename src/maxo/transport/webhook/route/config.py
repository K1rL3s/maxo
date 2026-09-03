from collections import Counter
from collections.abc import Mapping

from maxo.transport.webhook.route.errors import (
    MissingRouteParamDeclarationError,
    RepeatedPathParamError,
    UnknownQueryParamReferenceError,
    UnusedRouteParamDeclarationError,
)
from maxo.transport.webhook.route.params import RouteParam
from maxo.transport.webhook.route.path import PathTemplate
from maxo.transport.webhook.route.query import QuerySpec


def validate_route_config(
    *,
    path_template: PathTemplate,
    params: Mapping[str, RouteParam],
    query: QuerySpec,
) -> None:
    declared_param_names = set(params)
    path_param_names = set(path_template.param_names)

    if repeated_path_params := [
        name for name, count in Counter(path_template.param_names).items() if count > 1
    ]:
        raise RepeatedPathParamError(
            path=path_template.value,
            repeated_params=repeated_path_params,
        )

    if missing_params := path_param_names - declared_param_names:
        raise MissingRouteParamDeclarationError(
            path=path_template.value,
            missing_params=missing_params,
        )

    if unused_params := declared_param_names - path_param_names:
        raise UnusedRouteParamDeclarationError(
            path=path_template.value,
            unused_params=unused_params,
        )

    if unknown_query_param_refs := query.required_params() - path_param_names:
        raise UnknownQueryParamReferenceError(
            path=path_template.value,
            unknown_params=unknown_query_param_refs,
        )
