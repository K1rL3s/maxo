from unihttp.http import HTTPResponse
from unihttp.method import BaseMethod

from maxo.errors.api import raise_api_error
from maxo.types.base import MaxoType


class MaxoMethod[MethodResultT](BaseMethod[MethodResultT], MaxoType):
    """
    Базовый метод для методов Bot API Max.
    """

    def validate_response(self, response: HTTPResponse) -> None:
        data = response.data
        if (
            response.ok
            and isinstance(data, dict)
            and (data.get("error_code") or data.get("success") is False)
        ):
            raise_api_error(400, data)
