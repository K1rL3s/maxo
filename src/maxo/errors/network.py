from maxo.errors.base import MaxoError


class MaxBotNetworkError(MaxoError):
    message: str

    def __str__(self) -> str:
        return self.message


class MaxBotTimeoutError(MaxBotNetworkError):
    pass


class MaxBotRequestError(MaxoError):
    """Запрос не отправить: кривой URL, цикл редиректов и т.п. Повтор не поможет."""

    message: str

    def __str__(self) -> str:
        return self.message
