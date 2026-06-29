"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/fsm/context.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

from collections.abc import MutableMapping
from typing import Any

from maxo.fsm.key_builder import StorageKey
from maxo.fsm.state import State
from maxo.fsm.storages.base import BaseStorage


class FSMContext:
    __slots__ = ("key", "storage")

    def __init__(self, storage: BaseStorage, key: StorageKey) -> None:
        self.key = key
        self.storage = storage

    async def set_state(self, state: State | None = None) -> None:
        await self.storage.set_state(key=self.key, state=state)

    async def get_state(self) -> str | None:
        return await self.storage.get_state(key=self.key)

    async def set_data(self, data: MutableMapping[str, Any]) -> None:
        await self.storage.set_data(key=self.key, data=data)

    async def get_data(self) -> MutableMapping[str, Any]:
        return await self.storage.get_data(key=self.key)

    async def get_value(self, key: str, default: Any | None = None) -> Any | None:
        return await self.storage.get_value(
            storage_key=self.key,
            value_key=key,
            default=default,
        )

    async def update_data(
        self,
        data: MutableMapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> MutableMapping[str, Any]:
        if data:
            kwargs.update(data)
        return await self.storage.update_data(key=self.key, data=kwargs)

    async def clear(self) -> None:
        await self.set_state(state=None)
        await self.set_data({})
