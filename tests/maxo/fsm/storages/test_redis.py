from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import pytest

from maxo.fsm.key_builder import StorageKeyType
from maxo.fsm.state import State
from maxo.fsm.storages import redis as redis_storage
from maxo.fsm.storages.redis import RedisEventIsolation, RedisStorage

from .conftest import make_key


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str | bytes] = {}
        self.set_calls: list[tuple[str, str, Any | None]] = []
        self.delete_calls: list[str] = []
        self.lock_calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    async def set(self, key: str, value: str, ex: Any | None = None) -> None:
        self.values[key] = value
        self.set_calls.append((key, value, ex))

    async def get(self, key: str) -> str | bytes | None:
        return self.values.get(key)

    async def delete(self, key: str) -> None:
        self.values.pop(key, None)
        self.delete_calls.append(key)

    async def aclose(self) -> None:
        self.closed = True

    @asynccontextmanager
    async def lock(self, **kwargs: Any) -> AsyncIterator[None]:
        name = cast(str, kwargs["name"])
        self.lock_calls.append((name, kwargs))
        yield


def make_storage(
    redis: FakeRedis,
    *,
    state_ttl: int | None = None,
    data_ttl: int | None = None,
) -> RedisStorage:
    return RedisStorage(
        redis=cast(Any, redis),
        state_ttl=state_ttl,
        data_ttl=data_ttl,
    )


async def test_redis_storage_state_roundtrip_and_delete() -> None:
    redis = FakeRedis()
    storage = make_storage(redis, state_ttl=10)
    key = make_key()
    built_key = storage.key_builder.build(key, StorageKeyType.STATE)

    assert await storage.get_state(key) is None

    await storage.set_state(key, State("state", group_name="Group"))

    assert redis.set_calls == [(built_key, "Group:state", 10)]
    assert await storage.get_state(key) == "Group:state"

    redis.values[built_key] = b"Bytes:state"

    assert await storage.get_state(key) == "Bytes:state"

    await storage.set_state(key)

    assert redis.delete_calls == [built_key]


async def test_redis_storage_data_roundtrip_and_delete() -> None:
    redis = FakeRedis()
    storage = make_storage(redis, data_ttl=20)
    key = make_key()
    built_key = storage.key_builder.build(key, StorageKeyType.DATA)

    assert await storage.get_data(key) == {}

    await storage.set_data(key, {"foo": "bar"})

    assert redis.set_calls == [(built_key, '{"foo": "bar"}', 20)]
    assert await storage.get_data(key) == {"foo": "bar"}

    redis.values[built_key] = b'{"bytes": true}'

    assert await storage.get_data(key) == {"bytes": True}

    await storage.set_data(key, {})

    assert redis.delete_calls == [built_key]


async def test_redis_storage_update_data_and_close() -> None:
    redis = FakeRedis()
    storage = make_storage(redis)
    key = make_key()

    assert await storage.update_data(key, {"foo": "bar"}) == {"foo": "bar"}
    assert await storage.get_value(key, "foo") == "bar"

    await storage.close()

    assert redis.closed is True


async def test_redis_storage_create_isolation_uses_same_redis_and_builder() -> None:
    redis = FakeRedis()
    storage = make_storage(redis)

    isolation = storage.create_isolation(lock_kwargs={"timeout": 1})

    assert isinstance(isolation, RedisEventIsolation)
    isolation_redis = cast(Any, isolation.redis)
    assert isolation_redis is redis
    assert isolation.key_builder is storage.key_builder
    assert isolation.lock_kwargs == {"timeout": 1}


async def test_redis_event_isolation_lock_and_close() -> None:
    redis = FakeRedis()
    isolation = RedisEventIsolation(redis=cast(Any, redis))
    key = make_key()

    entered = False
    async with isolation.lock(key):
        entered = True

    assert entered is True
    built_key = isolation.key_builder.build(key, StorageKeyType.LOCK)
    assert redis.lock_calls == [
        (
            built_key,
            {
                "name": built_key,
                "timeout": 60,
                "lock_class": cast(Any, redis_storage).Lock,
            },
        ),
    ]

    await isolation.close()

    assert redis.closed is True


def test_redis_storage_from_url(monkeypatch: pytest.MonkeyPatch) -> None:
    pool = object()
    redis = FakeRedis()

    class FakeConnectionPool:
        @classmethod
        def from_url(cls, url: str, **kwargs: Any) -> object:
            assert url == "redis://localhost/0"
            assert kwargs == {"decode_responses": True}
            return pool

    def fake_redis_factory(connection_pool: object) -> FakeRedis:
        assert connection_pool is pool
        return redis

    monkeypatch.setattr(redis_storage, "ConnectionPool", FakeConnectionPool)
    monkeypatch.setattr(redis_storage, "Redis", fake_redis_factory)

    storage = RedisStorage.from_url(
        "redis://localhost/0",
        connection_kwargs={"decode_responses": True},
        state_ttl=30,
    )

    storage_redis = cast(Any, storage.redis)
    assert storage_redis is redis
    assert storage.state_ttl == 30


def test_redis_storage_declares_slots() -> None:
    """Regression test for #293: RedisStorage diverged from MemoryStorage,
    which declares __slots__, by not declaring its own -- silently falling
    back to a per-instance __dict__. `slotscheck` doesn't catch this because
    it only checks that a subclass doesn't *break* slots inherited from a
    parent, not that a sibling implementation of the same interface opted in.
    """
    redis = FakeRedis()
    storage = make_storage(redis)

    assert not hasattr(storage, "__dict__")

    with pytest.raises(AttributeError):
        cast(Any, storage).unexpected_attribute = "value"
