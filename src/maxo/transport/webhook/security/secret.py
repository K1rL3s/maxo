import re
from abc import ABC, abstractmethod
from hmac import compare_digest
from typing import Any, Final

from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.web.base import WebRequest

SECRET_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{5,256}$")
SECRET_HEADER: Final[str] = "x-max-bot-api-secret"  # noqa: S105


class BaseSecret(ABC):
    """Base class for secret verification in webhook requests."""

    async def verify(
        self,
        request: WebRequest[Any],
        route_params: RouteParams,
    ) -> bool:
        """
        Verify the incoming secret from the request.

        :param request: The webhook request object.
        :param route_params: Route parameters mapping.
        :return: True if the token is valid, False otherwise.
        """
        incoming_secret = request.headers.get(SECRET_HEADER)
        if incoming_secret is None:
            return False
        bot_token = route_params.get("bot_token")
        return compare_digest(
            incoming_secret,
            await self.secret(
                bot_token=bot_token if isinstance(bot_token, str) else None,
            ),
        )

    @abstractmethod
    async def secret(self, bot_token: str | None) -> str:
        """
        Return the webhook secret associated with the given bot token.

        :param bot_token: The bot token identifying the target bot, or None if
            the route does not expose one (e.g. not yet resolved, or single-bot route).
        :return: The secret string for this bot.
        """
        raise NotImplementedError


class StaticSecret(BaseSecret):
    """
    Static secret implementation for webhook security.

    Token format: 5-256 characters, only `^[a-zA-Z0-9_-]{5,256}$` are allowed.
    See: https://dev.max.ru/docs-api/methods/POST/subscriptions
    """

    def __init__(self, secret: str) -> None:
        if not SECRET_PATTERN.match(secret):
            raise ValueError(
                "Invalid secret format. "
                "Must be 5-256 characters, only ^[a-zA-Z0-9_-]{5,256}$.",
            )
        self.__secret = secret

    async def secret(self, bot_token: str | None) -> str:
        """
        Return the static secret.

        :param bot_token: Unused for static tokens.
        :return: The configured secret.
        """
        return self.__secret
