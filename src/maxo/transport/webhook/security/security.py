from typing import Any

from maxo import Bot
from maxo.omit import Omittable, Omitted
from maxo.transport.webhook.adapters.base_adapter import BoundRequest
from maxo.transport.webhook.security.base_check import SecurityCheck
from maxo.transport.webhook.security.secret_token import SecretToken


class Security:
    """
    Security management for webhook requests.

    Provides methods to verify requests and manage secret tokens.
    """

    def __init__(
        self,
        *checks: SecurityCheck,
        secret_token: SecretToken | None = None,
    ) -> None:
        self._secret_token = secret_token
        self._checks: tuple[SecurityCheck, ...] = checks

    async def verify(self, bot: Bot, bound_request: BoundRequest[Any]) -> bool:
        """
        Verify the security of a webhook request.

        :return: True if the request passes security checks, False otherwise.
        """
        if self._secret_token is not None:
            ok = await self._secret_token.verify(bot=bot, bound_request=bound_request)
            if not ok:
                return False

        for checker in self._checks:
            if not await checker.verify(bot=bot, bound_request=bound_request):
                return False

        return True

    async def get_secret_token(self, *, bot: Bot) -> Omittable[str]:
        """
        Get the secret token for the given bot, if configured.

        :return: The secret token as a string.
        """
        if self._secret_token is None:
            return Omitted()
        return self._secret_token.secret_token(bot=bot)
