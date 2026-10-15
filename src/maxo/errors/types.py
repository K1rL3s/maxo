from typing import Any

from maxo.errors.base import MaxoError


class AttributeIsEmptyError(MaxoError, AttributeError):
    obj: Any
    attr: str

    def __str__(self) -> str:
        return (
            f"{self.obj.__class__.__name__}.{self.attr} "
            f"is empty ({getattr(self.obj, self.attr)!r})"
        )
