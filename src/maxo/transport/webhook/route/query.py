from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hmac import compare_digest
from typing import TypeAlias

from maxo.transport.webhook.route.errors import (
    MissingQueryParamError,
    QueryParamMismatchError,
    RouteConfigError,
    UnexpectedQueryParamError,
)
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.web.base import QueryParams


class QueryValue(ABC):
    @abstractmethod
    def render(self, params: RouteParams) -> str:
        raise NotImplementedError

    @abstractmethod
    def required_params(self) -> frozenset[str]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Ref(QueryValue):
    """
    Query value copied from route params.

    Example:
        query={"bot_id": Ref("bot_id")}

    """

    name: str

    def render(self, params: RouteParams) -> str:
        return str(params[self.name])

    def required_params(self) -> frozenset[str]:
        return frozenset((self.name,))


@dataclass(frozen=True, slots=True)
class Const(QueryValue):
    """
    Static query value.

    Usually created internally from str/int.
    """

    value: str

    def render(self, params: RouteParams) -> str:
        return self.value

    def required_params(self) -> frozenset[str]:
        return frozenset()


QueryScalar: TypeAlias = QueryValue | str | int
QueryInput: TypeAlias = QueryScalar | list[QueryScalar] | tuple[QueryScalar, ...]


@dataclass(frozen=True, slots=True)
class QuerySpec:
    items: tuple[tuple[str, tuple[QueryValue, ...]], ...]
    names: frozenset[str]

    @classmethod
    def from_mapping(cls, query: Mapping[str, QueryInput] | None) -> "QuerySpec":
        items = normalize_query(query or {})
        return cls(
            items=items,
            names=frozenset(name for name, _ in items),
        )

    def __bool__(self) -> bool:
        return bool(self.items)

    def required_params(self) -> frozenset[str]:
        required: set[str] = set()
        for _, values in self.items:
            for value in values:
                required.update(value.required_params())
        return frozenset(required)

    def build_items(self, params: RouteParams) -> tuple[tuple[str, str], ...]:
        return tuple(
            (name, value.render(params))
            for name, values in self.items
            for value in values
        )

    def match(
        self,
        *,
        query_params: QueryParams,
        route_params: RouteParams,
        strict: bool = False,
    ) -> None:
        for name, expected_values in self.items:
            actual = [str(value) for value in query_params.getall(name, ())]

            if not actual:
                raise MissingQueryParamError(
                    query_param=name,
                    available_query_params=query_params.keys(),
                )

            expected = [value.render(route_params) for value in expected_values]

            if not query_values_match(actual, expected):
                raise QueryParamMismatchError(
                    query_param=name,
                    expected=expected,
                    got=actual,
                )

        if strict and (
            unexpected_query_params := set(query_params.keys()) - self.names
        ):
            raise UnexpectedQueryParamError(
                query_params=unexpected_query_params,
                expected_query_params=self.names,
            )


def query_values_match(actual: Sequence[str], expected: Sequence[str]) -> bool:
    if len(actual) == 1 and len(expected) == 1:
        return compare_digest(actual[0].encode(), expected[0].encode())

    return sorted(actual) == sorted(expected)


def normalize_query(
    query: Mapping[str, QueryInput],
) -> tuple[tuple[str, tuple[QueryValue, ...]], ...]:
    normalized: list[tuple[str, tuple[QueryValue, ...]]] = []

    for name, value in query.items():
        if isinstance(value, QueryValue):
            normalized.append((name, (value,)))
            continue

        if isinstance(value, (str, int)):
            normalized.append((name, (Const(str(value)),)))
            continue

        if not isinstance(value, list | tuple):
            raise RouteConfigError(
                message=f"Invalid Route config: query param has unsupported value. Param: {name!r}.",  # noqa: E501
            )

        if len(value) == 0:
            raise RouteConfigError(
                message=f"Invalid Route config: query param must contain at least one value. Param: {name!r}.",  # noqa: E501
            )

        values: list[QueryValue] = []
        for item in value:
            if isinstance(item, QueryValue):
                values.append(item)
            elif isinstance(item, (str, int)):
                values.append(Const(str(item)))
            else:
                raise RouteConfigError(
                    message=f"Invalid Route config: query param has unsupported list item. Param: {name!r}.",  # noqa: E501
                )

        normalized.append((name, tuple(values)))

    return tuple(normalized)
