"""Исключения maxo. Алиас `maxo.errors` для портирования ботов с `aiogram`."""

from maxo.errors.api import (
    MaxBotApiError,
    MaxBotBadGatewayError,
    MaxBotBadRequestError,
    MaxBotClientError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotServerError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
    RetvalReturnedServerException,
)
from maxo.errors.base import MaxoError
from maxo.errors.network import MaxBotNetworkError, MaxBotTimeoutError
from maxo.errors.routing import CycleRoutersError
from maxo.errors.subscriptions import UnsubscribeError
from maxo.errors.types import AttributeIsEmptyError

__all__ = (
    "AttributeIsEmptyError",
    "CycleRoutersError",
    "MaxBotApiError",
    "MaxBotBadGatewayError",
    "MaxBotBadRequestError",
    "MaxBotClientError",
    "MaxBotForbiddenError",
    "MaxBotMethodNotAllowedError",
    "MaxBotNetworkError",
    "MaxBotNotFoundError",
    "MaxBotServerError",
    "MaxBotServiceUnavailableError",
    "MaxBotTimeoutError",
    "MaxBotTooManyRequestsError",
    "MaxBotUnauthorizedError",
    "MaxBotUnknownServerError",
    "MaxBotUnsupportedMediaTypeError",
    "MaxoError",
    "RetvalReturnedServerException",
    "UnsubscribeError",
)
