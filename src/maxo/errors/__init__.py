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
    RetvalReturnedError,
)
from maxo.errors.base import MaxoError
from maxo.errors.network import MaxBotNetworkError, MaxBotTimeoutError
from maxo.errors.payload import InvalidPayloadError
from maxo.errors.routing import CycleRoutersError, RouterAlreadyIncludedError
from maxo.errors.subscriptions import UnsubscribeError
from maxo.errors.types import AttributeIsEmptyError
from maxo.errors.webapp import InvalidWebAppInitDataError

__all__ = (
    "AttributeIsEmptyError",
    "CycleRoutersError",
    "InvalidPayloadError",
    "InvalidWebAppInitDataError",
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
    "RetvalReturnedError",
    "RouterAlreadyIncludedError",
    "UnsubscribeError",
)
