import logging
from collections.abc import Iterable

from maxo.transport.webhook.errors import MaxoWebhookError


def format_names(names: Iterable[str]) -> str:
    return ", ".join(repr(name) for name in sorted(names))


class EngineError(MaxoWebhookError):
    code = "engine_error"


class BotStartError(EngineError):
    code = "engine_bot_start_failed"
    status_code = 502
    public_detail = "Bad gateway"
    log_level = logging.ERROR

    original_error: BaseException

    def __str__(self) -> str:
        return f"Failed to start webhook bot: {self.original_error}"


class BotNotFoundError(EngineError):
    code = "engine_bot_not_found"
    status_code = 404
    public_detail = "Not found"
    log_level = logging.INFO

    route_param_names: Iterable[str]

    def __post_init__(self) -> None:
        self.route_param_names = tuple(sorted(self.route_param_names))

    def __str__(self) -> str:
        return (
            "Webhook bot was not found. "
            f"Route param names: {format_names(self.route_param_names)}."
        )


class InvalidJsonError(EngineError):
    code = "engine_invalid_json"
    status_code = 400
    public_detail = "Bad request"
    log_level = logging.ERROR

    original_error: BaseException | None = None

    def __str__(self) -> str:
        message = "Invalid webhook JSON payload."

        if self.original_error is not None:
            message += f" Original error type: {type(self.original_error).__name__}."

        return message


class RequestHandlingStoppedError(EngineError):
    code = "engine_request_handling_stopped"
    status_code = 503
    public_detail = "Service unavailable"
    log_level = logging.DEBUG

    def __str__(self) -> str:
        return "Webhook engine is shutting down and no longer accepts requests."
