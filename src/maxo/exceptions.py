"""Исключения maxo. Алиас `maxo.errors` для портирования ботов с `aiogram`."""

from maxo.errors.api import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
    RetvalReturnedServerException,
)
from maxo.errors.base import MaxoError
from maxo.errors.routing import CycleRoutersError
from maxo.errors.types import AttributeIsEmptyError

__all__ = (
    "AttributeIsEmptyError",
    "CycleRoutersError",
    "MaxBotApiError",
    "MaxBotBadRequestError",
    "MaxBotForbiddenError",
    "MaxBotMethodNotAllowedError",
    "MaxBotNotFoundError",
    "MaxBotServiceUnavailableError",
    "MaxBotTooManyRequestsError",
    "MaxBotUnauthorizedError",
    "MaxBotUnknownServerError",
    "MaxBotUnsupportedMediaTypeError",
    "MaxoError",
    "RetvalReturnedServerException",
)
