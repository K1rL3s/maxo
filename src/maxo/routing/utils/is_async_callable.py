import inspect
from collections.abc import Callable
from typing import Any


def is_async_callable(obj: Callable[..., Any]) -> bool:
    """
    Проверяет, вернёт ли вызов объекта корутину.

    В отличие от :func:`inspect.iscoroutinefunction` понимает экземпляры
    классов с ``async def __call__``: сам объект корутинной функцией не
    является, ей является его ``__call__``.
    """
    unwrapped = inspect.unwrap(obj)
    return inspect.iscoroutinefunction(unwrapped) or inspect.iscoroutinefunction(
        type(unwrapped).__call__,
    )
