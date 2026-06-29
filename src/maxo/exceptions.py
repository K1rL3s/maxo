# ruff: noqa: E402

import warnings

warnings.warn(
    "Алиас `maxo.exceptions` сделан для удобного портирования ботов с `aiogram` "
    "и будет удален в будущих версиях. "
    "Пожалуйста, обновите импорты на 'from maxo.errors import ...'",
    FutureWarning,
    stacklevel=2,
)

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
