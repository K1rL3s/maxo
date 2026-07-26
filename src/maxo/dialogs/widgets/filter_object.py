import asyncio
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any, cast

from maxo.dialogs.integrations.magic_filter import DialogMagic
from maxo.routing.interfaces import Filter
from maxo.routing.utils.callback_params import get_callback_params

CallbackType = Callable[..., Any]
CallbackVariant = CallbackType | DialogMagic


@dataclass
class CallableObject:
    callback: CallbackVariant
    awaitable: bool = field(init=False)
    params: set[str] = field(init=False)
    varkw: bool = field(init=False)

    def _callable(self) -> CallbackType:
        # FilterObject.__post_init__ раскрывает DialogMagic,
        # но тип поля остаётся CallbackVariant
        return cast(CallbackType, self.callback)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self._callable())
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(
            callback,
        )
        self.params, self.varkw = get_callback_params(callback)

    def _prepare_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self.varkw:
            return kwargs

        return {k: kwargs[k] for k in self.params if k in kwargs}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        # потому что update это первый аргумент в фильтрах и хендлерах
        kwargs.pop("update", None)
        wrapped = partial(self._callable(), *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()
        return await asyncio.to_thread(wrapped)


@dataclass
class FilterObject(CallableObject):
    magic: DialogMagic | None = None

    def __post_init__(self) -> None:
        callback = self.callback
        if isinstance(callback, DialogMagic):
            self.magic = callback
            # cast, иначе mypy сузит тип до сигнатуры `resolve`
            # и сочтёт проверку на `Filter` ниже недостижимой.
            self.callback = cast(CallbackType, callback.resolve)

        super().__post_init__()

        if isinstance(self.callback, Filter):
            self.awaitable = True
