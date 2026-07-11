import re
from abc import abstractmethod
from hmac import compare_digest
from typing import Any

from maxo import Bot
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.security.checks.check import SecurityCheck

SECRET_HEADER = "X-Max-Bot-Api-Secret"  # noqa: S105
SECRET_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9-]{5,256}$")


class SecretToken(SecurityCheck):
    """Abstract base class for secret token verification in webhook requests."""

    secret_header: str = SECRET_HEADER

    @abstractmethod
    def secret_token(self, bot: Bot) -> str:
        """Return the secret token for the given bot."""
        raise NotImplementedError


class StaticSecretToken(SecretToken):
    """
    Static secret token implementation for webhook security.

    Token format: 5-256 characters, only `A-Z, a-z, 0-9, -` are allowed.
    See: https://dev.max.ru/docs-api/methods/POST/subscriptions
    """

    def __init__(self, token: str) -> None:
        if not SECRET_TOKEN_PATTERN.match(token):
            raise ValueError(
                "Invalid secret token format. Must be 5-256 characters, "
                "only A-Z, a-z, 0-9, -",
            )
        self._token = token

    async def verify(
        self,
        bot: Bot,
        bound_request: BoundRequest[Any],
    ) -> bool:
        incoming = bound_request.headers.get(self.secret_header)
        if incoming is None:
            return False
        return compare_digest(incoming, self._token)

    def secret_token(self, bot: Bot) -> str:
        return self._token
