"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/fsm/storage/redis.py.

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

try:
    from redis.asyncio import ConnectionPool, Redis
    from redis.asyncio.lock import Lock
    from redis.typing import ExpiryT
except ImportError as e:
    e.add_note("* Please run `pip install maxo[redis]`")
    raise

import json
from collections.abc import AsyncIterator, Callable, MutableMapping
from contextlib import asynccontextmanager
from typing import Any, cast

from maxo.fsm import State
from maxo.fsm.key_builder import (
    BaseKeyBuilder,
    DefaultKeyBuilder,
    StorageKey,
    StorageKeyType,
)
from maxo.fsm.storages.base import BaseEventIsolation, BaseStorage


class RedisStorage(BaseStorage):
    def __init__(
        self,
        redis: Redis,
        key_builder: BaseKeyBuilder | None = None,
        state_ttl: ExpiryT | None = None,
        data_ttl: ExpiryT | None = None,
        json_loads: Callable[[Any], Any] = json.loads,
        json_dumps: Callable[[Any], str] = json.dumps,
    ) -> None:
        if key_builder is None:
            key_builder = DefaultKeyBuilder()

        self.redis = redis
        self.key_builder = key_builder
        self.state_ttl = state_ttl
        self.data_ttl = data_ttl
        self.json_loads = json_loads
        self.json_dumps = json_dumps

    async def set_state(self, key: StorageKey, state: State | None = None) -> None:
        built_key = self.key_builder.build(key, StorageKeyType.STATE)
        if state is None:
            await self.redis.delete(built_key)
        else:
            await self.redis.set(
                built_key,
                cast(str, state.state),
                ex=self.state_ttl,
            )

    async def get_state(self, key: StorageKey) -> str | None:
        built_key = self.key_builder.build(key, StorageKeyType.STATE)
        value = await self.redis.get(built_key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return cast(str | None, value)

    async def set_data(self, key: StorageKey, data: MutableMapping[str, Any]) -> None:
        built_key = self.key_builder.build(key, StorageKeyType.DATA)
        if not data:
            await self.redis.delete(built_key)
        else:
            await self.redis.set(
                built_key,
                self.json_dumps(data),
                ex=self.data_ttl,
            )

    async def get_data(self, key: StorageKey) -> MutableMapping[str, Any]:
        built_key = self.key_builder.build(key, StorageKeyType.DATA)
        value = await self.redis.get(built_key)
        if value is None:
            return {}

        if isinstance(value, bytes):
            value = value.decode("utf-8")

        return cast(MutableMapping[str, Any], self.json_loads(value))

    async def close(self) -> None:
        await self.redis.aclose()

    @classmethod
    def from_url(
        cls,
        url: str,
        connection_kwargs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "RedisStorage":
        if connection_kwargs is None:
            connection_kwargs = {}
        pool = ConnectionPool.from_url(url, **connection_kwargs)
        redis = Redis(connection_pool=pool)
        return cls(redis=redis, **kwargs)

    def create_isolation(self, **kwargs: Any) -> "RedisEventIsolation":
        return RedisEventIsolation(
            redis=self.redis,
            key_builder=self.key_builder,
            **kwargs,
        )


DEFAULT_REDIS_LOCK_KWARGS = {"timeout": 60}


class RedisEventIsolation(BaseEventIsolation):
    __slots__ = ("key_builder", "lock_kwargs", "redis")

    def __init__(
        self,
        redis: Redis,
        key_builder: BaseKeyBuilder | None = None,
        lock_kwargs: dict[str, Any] | None = None,
    ) -> None:
        if key_builder is None:
            key_builder = DefaultKeyBuilder()
        if lock_kwargs is None:
            lock_kwargs = DEFAULT_REDIS_LOCK_KWARGS

        self.redis = redis
        self.key_builder = key_builder
        self.lock_kwargs = lock_kwargs

    @asynccontextmanager
    async def lock(self, key: StorageKey) -> AsyncIterator[None]:
        redis_key = self.key_builder.build(key, StorageKeyType.LOCK)
        async with self.redis.lock(name=redis_key, **self.lock_kwargs, lock_class=Lock):
            yield

    async def close(self) -> None:
        await self.redis.aclose()
