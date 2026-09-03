from typing import Any, Protocol

from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.web.base import WebRequest


class SecurityCheck(Protocol):
    """Protocol for security check on webhook requests."""

    async def verify(
        self,
        request: WebRequest[Any],
        route_params: RouteParams,
    ) -> bool:
        """
        Perform a security check on the incoming webhook request.

        :param request: The webhook request to verify.
        :param route_params: Route parameters mapping for the request.
        :return: True if the check passes (allow the request), False otherwise (reject).
        """
        raise NotImplementedError
