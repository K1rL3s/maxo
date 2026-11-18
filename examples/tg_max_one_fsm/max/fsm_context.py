from typing import Any

from maxo.fsm.context import FSMContext
from maxo.fsm.key_builder import StorageKey
from maxo.fsm.storages.base import BaseEventIsolation, BaseStorage
from maxo.routing.ctx import Ctx
from maxo.routing.events import MaxoUpdate
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.fsm_context import (
    FSM_CONTEXT_KEY,
    FSM_CONTEXT_STATE_KEY,
    FSM_STORAGE_KEY,
    RAW_STATE_KEY,
)

from ..user_repo import DbUser


class SharedFSMContextMiddleware(BaseMiddleware[MaxoUpdate[Any]]):
    __slots__ = ("_events_isolation", "_storage")

    def __init__(
        self,
        storage: BaseStorage,
        events_isolation: BaseEventIsolation,
    ) -> None:
        self._storage = storage
        self._events_isolation = events_isolation

    async def __call__(
        self,
        update: MaxoUpdate[Any],
        ctx: Ctx,
        next: NextMiddleware[MaxoUpdate[Any]],
    ) -> Any:
        ctx[FSM_STORAGE_KEY] = self._storage

        current_user = ctx.get("current_user")
        if current_user is None:
            return await next(ctx)

        storage_key = self.make_storage_key(user=current_user)

        async with self._events_isolation.lock(key=storage_key):
            fsm_context = FSMContext(key=storage_key, storage=self._storage)
            ctx[FSM_CONTEXT_KEY] = fsm_context
            ctx[FSM_CONTEXT_STATE_KEY] = fsm_context
            ctx[RAW_STATE_KEY] = await fsm_context.get_state()

            return await next(ctx)

    def make_storage_key(
        self,
        user: DbUser,
    ) -> StorageKey:
        return StorageKey(bot_id=0, chat_id=user.shared_id, user_id=user.shared_id)
