from maxo.errors.state import StateError
from maxo.routing.interfaces.observer import ObserverState


class EmptyObserverState(ObserverState):
    def ensure_add_handler(self) -> None:
        return None

    def ensure_add_filter(self) -> None:
        return None


class StartedObserverState(ObserverState):
    def ensure_add_handler(self) -> None:
        raise StateError("Can't add handler after startup")

    def ensure_add_filter(self) -> None:
        raise StateError("Can't add filter after startup")
