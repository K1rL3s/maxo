import re
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from maxo.routing.ctx import Ctx
from maxo.routing.filters.base import BaseFilter
from maxo.types import BaseUpdate
from maxo.types.error_event import ErrorEvent

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_ExceptionT = TypeVar("_ExceptionT", bound=Exception)


class ExceptionTypeFilter(
    BaseFilter[ErrorEvent[_ExceptionT, _UpdateT]],
    Generic[_ExceptionT, _UpdateT],
):
    _handler: Callable[[Any], bool]

    __slots__ = ("_handler",)

    def __init__(self, *errors: type[_ExceptionT], use_subclass: bool = True) -> None:
        if not errors:
            raise ValueError("At least one exception type is required")
        if use_subclass:
            self._handler = lambda e: isinstance(e, errors)
        else:
            self._handler = lambda e: type(e) in errors

    async def __call__(self, update: ErrorEvent[Any, Any], ctx: Ctx) -> bool:
        return self._handler(update.error)


class ExceptionMessageFilter(
    BaseFilter[ErrorEvent[_ExceptionT, _UpdateT]],
    Generic[_ExceptionT, _UpdateT],
):
    __slots__ = ("_pattern",)

    def __init__(self, pattern: str | re.Pattern[str]) -> None:
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self._pattern = pattern

    def __str__(self) -> str:
        return self._signature_to_string(pattern=self._pattern)

    async def __call__(self, update: ErrorEvent[Any, Any], ctx: Ctx) -> bool:
        result = self._pattern.match(str(update.error))
        if not result:
            return False

        ctx["match_exception"] = result
        return True
