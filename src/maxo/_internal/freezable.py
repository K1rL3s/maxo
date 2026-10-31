from maxo.errors.routing import RoutingFrozenError


class Freezable:
    __slots__ = ("_frozen",)

    def __init__(self) -> None:
        self._frozen = False

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False

    def _ensure_not_frozen(self, message: str) -> None:
        if self._frozen:
            raise RoutingFrozenError(message)
