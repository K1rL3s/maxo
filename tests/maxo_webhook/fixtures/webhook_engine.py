from collections.abc import Mapping, MutableMapping
from typing import Any

from maxo import Bot
from maxo.routing.dispatcher import Dispatcher
from maxo.transport.webhook.engines.base import BaseWebhookEngine
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.route.route import Route
from maxo.transport.webhook.tasks import TaskTracker
from maxo.transport.webhook.web.base import WebAdapter, WebRequest
from maxo.types import BaseUpdate


class DummyRoute(Route):
    path = "/webhook"

    def __init__(self, route_params: Mapping[str, str] | None = None) -> None:
        self.route_params = dict(route_params or {})

    async def match(self, request: WebRequest[Any]) -> RouteParams:
        return self.route_params

    async def build_url(self, bot: Bot) -> str:
        return f"https://example.test/webhook/{bot.token}"


class CapturingAdapter(WebAdapter[Any, Any, Any]):
    def bind_request(self, request: Any) -> WebRequest[Any]:
        raise NotImplementedError

    def register(
        self,
        app: Any,
        path: str,
        handler: Any,
        *,
        on_startup: Any,
        on_shutdown: Any,
    ) -> None:
        raise NotImplementedError

    def json_response(
        self,
        status_code: int,
        data: dict[str, str] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": "json",
            "status_code": status_code,
            "data": data,
            "headers": headers,
        }

class DummyDispatcher(Dispatcher):
    def __init__(self, result: Any = None) -> None:
        self.workflow_data: MutableMapping[str, Any] = {}
        self.result = result
        self.webhook_bot: Bot | None = None
        self.webhook_update: BaseUpdate | None = None

    async def feed_update(self, update: BaseUpdate, bot: Bot | None = None) -> Any:
        self.webhook_bot = bot
        self.webhook_update = update
        return self.result

    async def feed_signal(self, signal: Any, bot: Bot | None = None) -> None:
        return None


class SpyEngine(BaseWebhookEngine[Any, Any, Any]):
    """Records lifecycle callbacks so tests can assert on their order."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        bot: Bot | None,
        events: list[Any],
        *,
        web: WebAdapter[Any, Any, Any],
        route: Route,
    ) -> None:
        self.bot = bot
        self.events = events
        self._task_tracker = TaskTracker()

        super().__init__(dispatcher, web=web, route=route)

    async def _on_startup(self, app: Any, *args: Any, **kwargs: Any) -> None:
        self.events.append(("engine_startup", app))

    async def _on_shutdown(self, app: Any, *args: Any, **kwargs: Any) -> None:
        self.events.append(("engine_shutdown", app))

    async def _resolve_bot(self, route_params: RouteParams) -> Bot | None:
        return self.bot

    def _get_task_tracker(self, bot: Bot) -> TaskTracker:
        return self._task_tracker
