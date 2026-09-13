from typing import Any

from unihttp.http import HTTPResponse
from unihttp.method import BaseMethod, StreamMethod

from maxo import loggers
from maxo.errors.api import raise_api_error
from maxo.types.base import MaxoType


class MaxoMethod[MethodResultT](BaseMethod[MethodResultT], MaxoType):
    """
    Базовый метод для методов Bot API Max.
    """

    def validate_response(self, response: HTTPResponse[Any]) -> None:
        """MAX иногда отвечает 200 с `success: false`/`error_code` в теле."""
        if (
            response.ok
            and isinstance(response.data, dict)
            and (
                response.data.get("error_code")
                or response.data.get("success", None) is False
            )
        ):
            loggers.bot_session.warning(
                "Patch the status code from %d to 400 due to an error on the MAX API: %r",
                response.status_code,
                response.data,
            )
            response.status_code = 400

    def on_error(self, response: HTTPResponse[Any]) -> None:
        raise_api_error(response.status_code, response.data)


class MaxoStreamMethod(StreamMethod, MaxoType):
    """Базовый метод для стриминговых методов Bot API Max."""

    def on_error(self, response: HTTPResponse[Any]) -> None:
        raise_api_error(response.status_code, None)
