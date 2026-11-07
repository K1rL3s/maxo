from maxo.errors.base import MaxoError


class StateError(MaxoError):
    message: str

    def __str__(self) -> str:
        return self.message
