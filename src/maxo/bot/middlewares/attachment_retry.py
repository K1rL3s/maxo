from typing import Any

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.middlewares import AsyncHandler, AsyncMiddleware

from maxo.backoff import Backoff, BackoffConfig
from maxo.errors.api import MaxBotBadRequestError

NOT_READY_CODE = "attachment.not.ready"
NOT_READY_MESSAGE_MARK = "not.processed"


def is_attachment_not_ready(error: MaxBotBadRequestError) -> bool:
    if NOT_READY_CODE in {error.code or "", error.error or ""}:
        return True
    return NOT_READY_MESSAGE_MARK in (error.message or "")


class AttachmentNotReadyRetryMiddleware(AsyncMiddleware):
    """Ретраит `attachment.not.ready` с backoff."""

    __slots__ = ("_backoff_config", "_max_retries")

    def __init__(self, max_retries: int, backoff_config: BackoffConfig) -> None:
        self._max_retries = max_retries
        self._backoff_config = backoff_config

    async def handle(
        self,
        request: HTTPRequest,
        next_handler: AsyncHandler,
    ) -> HTTPResponse[Any]:
        backoff = Backoff(self._backoff_config)

        while True:
            try:
                return await next_handler(request)
            except MaxBotBadRequestError as error:
                if (
                    not is_attachment_not_ready(error)
                    or backoff.counter >= self._max_retries
                ):
                    raise
                backoff.next()
                await backoff.sleep()
