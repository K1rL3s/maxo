from maxo.errors.state import StateError
from maxo.routing.interfaces.router import RouterState


class EmptyRouterState(RouterState):
    def ensure_include(self) -> None:
        return None


class StartedRouterState(RouterState):
    def ensure_include(self) -> None:
        raise StateError("Routers cannot be include after startup")
