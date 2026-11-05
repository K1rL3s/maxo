import re
from abc import abstractmethod
from hmac import compare_digest
from typing import Any

from maxo import Bot
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.security.base_check import SecurityCheck

SECRET_HEADER = "X-Max-Bot-Api-Secret"  # noqa: S105
SECRET_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_-]{5,256}")


class SecretToken(SecurityCheck):
    """Abstract base class for secret token verification in webhook requests."""

    secret_header: str = SECRET_HEADER

    @abstractmethod
    def secret_token(self, bot: Bot) -> str:
        """Return the secret token for the given bot."""
        raise NotImplementedError


class StaticSecretToken(SecretToken):
    """
    Статический секретный токен вебхука.

    Формат токена: от 5 до 256 символов, допустимы только `A-Z, a-z, 0-9, _, -`.
    См.: https://dev.max.ru/docs-api/methods/POST/subscriptions
    """

    def __init__(self, token: str) -> None:
        if not SECRET_TOKEN_PATTERN.fullmatch(token):
            raise ValueError(
                "Invalid secret token format. Must be 5-256 characters, "
                "only A-Z, a-z, 0-9, _, -",
            )
        self._token = token

    async def verify(
        self,
        bot: Bot,
        bound_request: BoundRequest[Any],
    ) -> bool:
        incoming = bound_request.headers.get(self.secret_header)
        if incoming is None or not SECRET_TOKEN_PATTERN.fullmatch(incoming):
            return False
        return compare_digest(incoming.encode("ascii"), self._token.encode("ascii"))

    def secret_token(self, bot: Bot) -> str:
        return self._token
