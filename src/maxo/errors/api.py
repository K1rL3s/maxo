from typing import Any

from maxo.errors.base import MaxoError


class MaxBotApiError(MaxoError):
    """Сервер возвращает это, если возникло исключение при вашем запросе."""

    code: str
    error: str
    message: str
    raw_data: Any = None

    def __str__(self) -> str:
        parts: list[str] = []
        if self.code:
            parts.append(f"code={self.code!r}")
        if self.error:
            parts.append(f"error={self.error!r}")
        if self.message:
            parts.append(f"message={self.message!r}")
        if self.raw_data and not parts:
            parts.append(f"raw_data={self.raw_data!r}")

        return f"{self.__class__.__name__}({', '.join(parts)})"


class MaxBotBadRequestError(MaxBotApiError): ...


class MaxBotForbiddenError(MaxBotApiError): ...


class MaxBotUnauthorizedError(MaxBotApiError): ...


class MaxBotNotFoundError(MaxBotApiError): ...


class MaxBotMethodNotAllowedError(MaxBotApiError): ...


class MaxBotUnsupportedMediaTypeError(MaxBotApiError): ...


class MaxBotTooManyRequestsError(MaxBotApiError): ...


class MaxBotUnknownServerError(MaxBotApiError): ...


class MaxBotServiceUnavailableError(MaxBotApiError): ...


class RetvalReturnedServerException(MaxoError): ...
