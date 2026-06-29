import asyncio
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Any

from maxo.dialogs.integrations.magic_filter import DialogMagic
from maxo.routing.interfaces import Filter

CallbackType = Callable[..., Any]


@dataclass
class CallableObject:
    callback: CallbackType
    awaitable: bool = field(init=False)
    params: set[str] = field(init=False)
    varkw: bool = field(init=False)

    def __post_init__(self) -> None:
        callback = inspect.unwrap(self.callback)
        self.awaitable = inspect.isawaitable(callback) or inspect.iscoroutinefunction(
            callback,
        )
        spec = inspect.getfullargspec(callback)
        self.params = {*spec.args, *spec.kwonlyargs}
        self.varkw = spec.varkw is not None

    def _prepare_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        if self.varkw:
            return kwargs

        return {k: kwargs[k] for k in self.params if k in kwargs}

    async def call(self, *args: Any, **kwargs: Any) -> Any:
        # потому что update это первый аргумент в фильтрах и хендлерах
        kwargs.pop("update", None)
        wrapped = partial(self.callback, *args, **self._prepare_kwargs(kwargs))
        if self.awaitable:
            return await wrapped()
        return await asyncio.to_thread(wrapped)


@dataclass
class FilterObject(CallableObject):
    magic: DialogMagic | None = None

    def __post_init__(self) -> None:
        if isinstance(self.callback, DialogMagic):
            self.magic = self.callback
            self.callback = self.callback.resolve

        super().__post_init__()

        if isinstance(self.callback, Filter):
            self.awaitable = True
