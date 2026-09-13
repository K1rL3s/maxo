from collections import defaultdict
from collections.abc import MutableMapping, MutableSequence
from typing import Any

from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.interfaces.router import BaseRouter
from maxo.types.base import BaseUpdate


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
        # https://github.com/K1rL3s/maxo/pull/85
        new_middlewares = {
            update_tp: list(current_middlewares)
            for update_tp, current_middlewares in middlewares.items()
        }
        resolve_middlewares(children_router, defaultdict(list, new_middlewares))


def _resolving_middlewares(
    router: BaseRouter,
    middlewares: MutableMapping[type[BaseUpdate], MutableSequence[BaseMiddleware[Any]]],
) -> None:
    for update_tp, observer in router.observers.items():
        new_inners = (*middlewares[update_tp],)
        current_inners = (*observer.middleware.inner.middlewares,)

        observer.middleware.inner.middlewares[:0] = new_inners
        middlewares[update_tp].extend(current_inners)
