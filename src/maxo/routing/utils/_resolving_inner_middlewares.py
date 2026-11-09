from collections import defaultdict
from collections.abc import MutableMapping, MutableSequence
from typing import Any

from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.interfaces.observer import Observer
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
    own_inners: dict[Observer[Any, Any, Any], tuple[BaseMiddleware[Any], ...]] = {}
    for update_tp, observer in router.observers.items():
        if observer not in own_inners:
            inner = observer.middleware.inner
            # Повторный Dispatcher.start вызывает этот resolve еще раз.
            # inherited_count - сколько своих же унаследованных мидлварей
            # мы вставили в начало на предыдущем старте: их нужно снять,
            # иначе унаследованное накопится еще раз (#347).
            if inner.inherited_count:
                del inner.middlewares[: inner.inherited_count]

            own_inners[observer] = (*inner.middlewares,)

            new_inherited = middlewares[update_tp]
            inner.middlewares[:0] = new_inherited
            inner.inherited_count = len(new_inherited)
        middlewares[update_tp].extend(own_inners[observer])
