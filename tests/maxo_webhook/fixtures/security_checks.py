from typing import Any

from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security.checks.check import SecurityCheck
from maxo.transport.webhook.web.base import WebRequest


class RecordingCheck(SecurityCheck):
    def __init__(self, name: str, *, result: bool, calls: list[str]) -> None:
        self.name = name
        self.result = result
        self.calls = calls

    async def verify(
        self,
        request: WebRequest[Any],
        route_params: RouteParams,
    ) -> bool:
        self.calls.append(self.name)
        return self.result
