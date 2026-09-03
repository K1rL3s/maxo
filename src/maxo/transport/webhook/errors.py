import logging
from typing import ClassVar

from maxo.errors import MaxoError


class MaxoWebhookError(MaxoError):
    code: ClassVar[str] = "webhook_error"
    status_code: ClassVar[int] = 500
    public_detail: ClassVar[str] = "Internal server error"
    log_level: ClassVar[int] = logging.ERROR

    def response_payload(self) -> dict[str, str]:
        return {"detail": self.public_detail}
