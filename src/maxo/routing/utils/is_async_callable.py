import inspect
from collections.abc import Callable
from typing import Any


def is_async_callable(obj: Callable[..., Any]) -> bool:
    unwrapped = inspect.unwrap(obj)
    call = type(unwrapped).__call__
    return any(
        inspect.iscoroutinefunction(candidate)
        for candidate in (obj, unwrapped, call, inspect.unwrap(call))
    )
