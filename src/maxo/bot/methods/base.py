from typing import Any

from unihttp.http import HTTPResponse
from unihttp.method import BaseMethod, StreamMethod

from maxo.errors.api import raise_api_error
from maxo.types.base import MaxoType


class MaxoMethod[MethodResultT](BaseMethod[MethodResultT], MaxoType):
    """
    Базовый метод для методов Bot API Max.
    """

    def validate_response(self, response: HTTPResponse[Any]) -> None:
        """MAX иногда отвечает 200 с `success: false`/`error_code` в теле."""
        data = response.data
        if (
            response.ok
            and isinstance(data, dict)
            and (data.get("error_code") or data.get("success") is False)
        ):
            raise_api_error(400, data)

    def on_error(self, response: HTTPResponse[Any]) -> None:
        raise_api_error(response.status_code, response.data)


class MaxoStreamMethod(StreamMethod, MaxoType):
    """Базовый метод для стриминговых методов Bot API Max."""

    def on_error(self, response: HTTPResponse[Any]) -> None:
        raise_api_error(response.status_code, None)
