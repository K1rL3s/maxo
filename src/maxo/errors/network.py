from maxo.errors.base import MaxoError


class MaxBotNetworkError(MaxoError):
    message: str

    def __str__(self) -> str:
        return self.message


class MaxBotTimeoutError(MaxBotNetworkError):
    pass


def to_network_error(error: Exception) -> MaxBotNetworkError:
    # У части исключений aiohttp пустой текст, тогда берём имя класса.
    message = str(error) or type(error).__name__
    if isinstance(error, TimeoutError):
        return MaxBotTimeoutError(message)
    return MaxBotNetworkError(message)


class MaxBotRequestError(MaxoError):
    """Запрос не отправить: кривой URL, цикл редиректов и т.п. Повтор не поможет."""

    message: str

    def __str__(self) -> str:
        return self.message
