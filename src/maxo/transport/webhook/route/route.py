from collections.abc import Mapping
from typing import Any, TypeVar
from urllib.parse import quote

from yarl import URL

from maxo import Bot
from maxo.transport.webhook.route.config import validate_route_config
from maxo.transport.webhook.route.errors import (
    InvalidPathParamError,
    MissingPathParamError,
    UnexpectedQueryParamError,
)
from maxo.transport.webhook.route.params import (
    RouteParam,
    RouteParamBinding,
    RouteParams,
)
from maxo.transport.webhook.route.path import PathTemplate
from maxo.transport.webhook.route.query import QueryInput, QuerySpec
from maxo.transport.webhook.route.url import prepare_base_url
from maxo.transport.webhook.web.base import WebRequest

RawRequestT = TypeVar("RawRequestT")


class Route:
    """Universal web route."""

    __slots__ = (
        "_base_url",
        "_path_params",
        "_path_template",
        "_query",
        "_strict_query",
    )

    def __init__(
        self,
        *,
        base_url: str | URL,
        path: str | URL = "/",
        params: Mapping[str, RouteParam] | None = None,
        query: Mapping[str, QueryInput] | None = None,
        strict_query: bool = False,
    ) -> None:
        base_url = prepare_base_url(base_url)
        path_template = PathTemplate.from_input(path)
        route_params = dict(params or {})
        query_spec = QuerySpec.from_mapping(query)

        validate_route_config(
            path_template=path_template,
            params=route_params,
            query=query_spec,
        )

        path_params = tuple(
            RouteParamBinding(name=name, param=route_params[name])
            for name in path_template.param_names
        )

        self._base_url = base_url
        self._path_template = path_template
        self._path_params = path_params
        self._query = query_spec
        self._strict_query = strict_query

    @property
    def path(self) -> str:
        """
        Get path template for route registration in a web framework.

        This is not a full URL, only the path part, for example "/webhook/{bot_id}".
        """
        return self._path_template.value

    async def build_url(self, bot: Bot) -> str:
        if self._path_params:
            route_params: dict[str, Any] = {}
            for binding in self._path_params:
                route_params[binding.name] = await binding.param.build(
                    bot=bot,
                    params=route_params,
                )

            path = self._path_template.build(
                {name: quote(value, safe="") for name, value in route_params.items()},
            )
        else:
            path = self._path_template.value
            route_params = {}

        url = self._base_url.joinpath(path.lstrip("/"), encoded=True)
        if self._query:
            url = url.with_query(self._query.build_items(route_params))
        return str(url)

    async def match(self, request: WebRequest[RawRequestT]) -> RouteParams:
        route_params: dict[str, Any] = {}
        request_path_params = request.path_params

        for binding in self._path_params:
            if binding.name not in request_path_params:
                raise MissingPathParamError(
                    param=binding.name,
                    available_params=request_path_params,
                )

            raw_value = request_path_params[binding.name]
            try:
                route_params[binding.name] = await binding.param.parse(
                    value=raw_value,
                    params=route_params,
                )
            except (TypeError, ValueError) as exc:
                raise InvalidPathParamError(
                    param=binding.name,
                    value=raw_value,
                ) from exc

        if self._query:
            self._query.match(
                query_params=request.query_params,
                route_params=route_params,
                strict=self._strict_query,
            )
        elif self._strict_query and request.query_params:
            raise UnexpectedQueryParamError(
                query_params=request.query_params.keys(),
                expected_query_params=(),
            )

        return route_params
