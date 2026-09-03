from maxo.errors.base import MaxoError


class UnsubscribeError(MaxoError):
    """Не удалось удалить WebHook-подписку."""

    url: str
    error: Exception

    def __str__(self) -> str:
        return f"Не удалось удалить WebHook-подписку {self.url!r}: {self.error}"
