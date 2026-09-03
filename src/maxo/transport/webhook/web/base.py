from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Generic, Protocol, TypeAlias, TypeVar

from multidict import CIMultiDictProxy, MultiMapping

AppT = TypeVar("AppT")
RawRequestT_co = TypeVar("RawRequestT_co", covariant=True)
RawRequestT = TypeVar("RawRequestT")
FrameworkResponseT = TypeVar("FrameworkResponseT")

LifecycleCallback: TypeAlias = Callable[..., Awaitable[None]]


Headers = CIMultiDictProxy[str]
QueryParams = MultiMapping[str]
PathParams = Mapping[str, str]


class WebRequest(Protocol[RawRequestT_co]):
    """Framework request behavior required by the web engine."""

    @property
    def raw(self) -> RawRequestT_co:
        """Return the original framework request."""
        ...

    @property
    def client_ip(self) -> str | None: ...

    async def json(self) -> dict[str, Any]: ...

    @property
    def headers(self) -> Headers: ...

    @property
    def query_params(self) -> QueryParams: ...

    @property
    def path_params(self) -> PathParams: ...


WebHandler: TypeAlias = Callable[
    [WebRequest[RawRequestT_co]],
    Awaitable[FrameworkResponseT],
]


class WebAdapter(ABC, Generic[AppT, RawRequestT, FrameworkResponseT]):
    """Integration boundary for a concrete web framework."""

    @abstractmethod
    def bind_request(self, request: RawRequestT) -> WebRequest[RawRequestT]:
        """Bind a framework request object to the engine request interface."""
        raise NotImplementedError

    @abstractmethod
    def register(
        self,
        app: AppT,
        path: str,
        handler: WebHandler[RawRequestT, FrameworkResponseT],
        *,
        on_startup: LifecycleCallback,
        on_shutdown: LifecycleCallback,
    ) -> None:
        """Register route and lifecycle callbacks in the framework app."""
        raise NotImplementedError

    @abstractmethod
    def json_response(
        self,
        status_code: int,
        data: dict[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> FrameworkResponseT:
        """Create a JSON response for the framework."""
        raise NotImplementedError
