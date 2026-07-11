from abc import ABC, abstractmethod
from typing import Any

from maxo import Bot
from maxo.transport.webhook.adapters.base_adapter import BoundRequest


class SecurityCheck(ABC):
    """Abstract class for security check on webhook requests."""

    @abstractmethod
    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        """
        Perform a security check.

        :return: True if the check passes, False otherwise.
        """
        raise NotImplementedError
