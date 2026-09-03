from typing import Any

from maxo import Bot
from maxo.transport.webhook.route.params import RouteParams
from maxo.transport.webhook.security.checks.check import SecurityCheck
from maxo.transport.webhook.security.errors import SecretError, SecurityCheckError
from maxo.transport.webhook.security.secret import BaseSecret
from maxo.transport.webhook.web.base import WebRequest


class Security:
    def __init__(
        self,
        *checks: SecurityCheck,
        secret: BaseSecret | None = None,
    ) -> None:
        self._secret = secret
        self._checks: tuple[SecurityCheck, ...] = checks

    async def verify(
        self,
        *,
        request: WebRequest[Any],
        route_params: RouteParams,
    ) -> None:
        if self._secret is not None:
            ok = await self._secret.verify(
                request=request,
                route_params=route_params,
            )
            if not ok:
                raise SecretError

        for check in self._checks:
            ok = await check.verify(
                request=request,
                route_params=route_params,
            )
            if not ok:
                raise SecurityCheckError(
                    security_check=check.__class__.__name__,
                    client_ip=str(request.client_ip)
                    if request.client_ip is not None
                    else None,
                )

    async def secret(self, bot: Bot) -> str | None:
        """
        Get the secret for a specific bot.

        :param bot: The resolved bot to get the secret for.
        :return: The secret string, or None if no secret is configured.
        """
        if self._secret is None:
            return None

        return await self._secret.secret(bot_token=bot.token)
