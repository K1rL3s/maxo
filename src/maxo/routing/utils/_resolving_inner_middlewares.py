from collections import defaultdict
from collections.abc import MutableMapping, MutableSequence
from typing import Any

from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.interfaces.router import BaseRouter
from maxo.routing.updates.base import BaseUpdate


def _resolving_middlewares(
    router: BaseRouter,
    middlewares: MutableMapping[
        type[BaseUpdate],
        MutableSequence[BaseMiddleware[Any]],
    ],
) -> None:
    for update_tp, observer in router.observers.items():
        new_inners = (*middlewares[update_tp],)
        current_inners = (*observer.middleware.inner.middlewares,)

        observer.middleware.inner.middlewares.extend(new_inners)
        middlewares[update_tp].extend(current_inners)


def _resolving_outer_middlewares(
    router: BaseRouter,
    middlewares: MutableMapping[
        type[BaseUpdate],
        MutableSequence[BaseMiddleware[Any]],
    ],
) -> None:
    for update_tp, observer in router.observers.items():
        new_middlewares = (*middlewares[update_tp],)
        current_middlewares = (*observer.middleware.outer.middlewares,)

        observer.middleware.outer.middlewares.extend(new_middlewares)
        middlewares[update_tp].extend(current_middlewares)


def resolve_middlewares(
    router: BaseRouter,
    middlewares: (
        MutableMapping[type[BaseUpdate], MutableSequence[BaseMiddleware[Any]]] | None
    ) = None,
) -> None:
    if middlewares is None:
        middlewares = defaultdict(list)

    _resolving_middlewares(router, middlewares)

    for children_router in router.children_routers:
        resolve_middlewares(
            children_router,
            middlewares.copy(),
        )
