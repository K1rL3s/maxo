from typing import Any, Never

from maxo.errors.base import MaxoError


class MaxBotApiError(MaxoError):
    """Сервер возвращает это, если возникло исключение при вашем запросе."""

    code: str
    error: str
    message: str
    raw_data: Any = None
    status_code: int | None = None

    def __str__(self) -> str:
        parts: list[str] = []
        if self.status_code is not None:
            parts.append(f"status_code={self.status_code}")
        if self.code:
            parts.append(f"code={self.code!r}")
        if self.error:
            parts.append(f"error={self.error!r}")
        if self.message:
            parts.append(f"message={self.message!r}")
        if self.raw_data and not (self.code or self.error or self.message):
            parts.append(f"raw_data={self.raw_data!r}")

        return f"{self.__class__.__name__}({', '.join(parts)})"


class MaxBotClientError(MaxBotApiError): ...


class MaxBotServerError(MaxBotApiError): ...


class MaxBotBadRequestError(MaxBotClientError): ...


class MaxBotForbiddenError(MaxBotClientError): ...


class MaxBotUnauthorizedError(MaxBotClientError): ...


class MaxBotNotFoundError(MaxBotClientError): ...


class MaxBotMethodNotAllowedError(MaxBotClientError): ...


class MaxBotUnsupportedMediaTypeError(MaxBotClientError): ...


class MaxBotTooManyRequestsError(MaxBotClientError): ...


class MaxBotUnknownServerError(MaxBotServerError): ...


class MaxBotBadGatewayError(MaxBotServerError): ...


class MaxBotServiceUnavailableError(MaxBotServerError): ...


class MaxBotResponseError(MaxoError):
    """
    В ответе API нет данных, без которых maxo не может продолжить.

    Например, токена загруженного файла. Скорее всего, MAX поменял формат.
    """

    method: str
    detail: str = ""
    raw_data: Any = None

    def __str__(self) -> str:
        text = f"Неожиданный ответ {self.method}"
        return f"{text}: {self.detail}" if self.detail else text


_ERRORS_BY_STATUS: dict[int, type[MaxBotApiError]] = {
    400: MaxBotBadRequestError,
    401: MaxBotUnauthorizedError,
    403: MaxBotForbiddenError,
    404: MaxBotNotFoundError,
    405: MaxBotMethodNotAllowedError,
    415: MaxBotUnsupportedMediaTypeError,
    429: MaxBotTooManyRequestsError,
    500: MaxBotUnknownServerError,
    502: MaxBotBadGatewayError,
    503: MaxBotServiceUnavailableError,
}


def api_error_type(status_code: int) -> type[MaxBotApiError]:
    error_type = _ERRORS_BY_STATUS.get(status_code)
    if error_type is not None:
        return error_type
    if status_code in range(400, 500):
        return MaxBotClientError
    if status_code in range(500, 600):
        return MaxBotServerError
    return MaxBotApiError


def raise_api_error(status_code: int, data: object) -> Never:
    if isinstance(data, dict):
        code = data.get("code") or data.get("error_code")
        error = data.get("error") or data.get("error_data")
        message = data.get("message")
    else:
        # Non-JSON body, e.g. an nginx error page
        code = error = None
        message = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
    raise api_error_type(status_code)(
        code=_to_str(code),
        error=_to_str(error),
        message=_to_str(message),
        raw_data=data,
        status_code=status_code,
    )


def _to_str(value: object) -> str:
    return "" if value is None else str(value)
