from collections.abc import MutableSequence
from copy import copy
from typing import overload

from maxo.errors.routing import CycleRoutersError
from maxo.routing.interfaces.router import BaseRouter


@overload
def validate_router_graph(router: BaseRouter) -> None: ...


@overload
def validate_router_graph(
    router: BaseRouter,
    visited_routers: MutableSequence[BaseRouter],
) -> None: ...


def validate_router_graph(
    router: BaseRouter,
    visited_routers: MutableSequence[BaseRouter] | None = None,
) -> None:
    if visited_routers is None:
        visited_routers = []

    visited_routers.append(router)

    for children_router in router.children_routers:
        if children_router in visited_routers:
            raise CycleRoutersError([*visited_routers, children_router])

        validate_router_graph(children_router, copy(visited_routers))
