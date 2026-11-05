from maxo.errors.base import MaxoError


class InvalidPayloadError(MaxoError, ValueError):
    """Payload не удалось декодировать через `decode_payload`."""

    payload: str

    def __str__(self) -> str:
        return f"Invalid encoded payload: {self.payload!r}"
