from typing import Any

from maxo import Bot
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.security.checks.check import SecurityCheck


class PassingCheck(SecurityCheck):
    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        return True


class FailingCheck(SecurityCheck):
    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        return False


class ConditionalCheck(SecurityCheck):
    def __init__(self, condition: bool):
        self.condition = condition

    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        return self.condition
