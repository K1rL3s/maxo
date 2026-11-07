from abc import abstractmethod
from typing import Protocol

from maxo.errors.state import StateError


class MiddlewareManagerState(Protocol):
    @abstractmethod
    def ensure_add_middleware(self) -> None:
        raise NotImplementedError


class EmptyMiddlewareManagerState(MiddlewareManagerState):
    def ensure_add_middleware(self) -> None:
        return None


class StartedMiddlewareManagerState(MiddlewareManagerState):
    def ensure_add_middleware(self) -> None:
        raise StateError("Can't add middleware after startup")
