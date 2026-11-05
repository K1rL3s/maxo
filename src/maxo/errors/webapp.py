from maxo.errors.base import MaxoError


class InvalidWebAppInitDataError(MaxoError, ValueError):
    """Init data мини-приложения не прошли проверку подписи или разбор."""

    message: str

    def __str__(self) -> str:
        return self.message
