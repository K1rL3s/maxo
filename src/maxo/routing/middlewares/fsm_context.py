from typing import Any

from maxo.fsm.context import FSMContext
from maxo.fsm.key_builder import StorageKey
from maxo.fsm.storages.base import BaseEventIsolation, BaseStorage
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.routing.signals.update import MaxoUpdate
from maxo.types.update_context import UpdateContext

FSM_STORAGE_KEY = "fsm_storage"
FSM_CONTEXT_KEY = "fsm_context"
FSM_CONTEXT_STATE_KEY = "state"  # same as "fsm_context", Подражание aiogram
RAW_STATE_KEY = "raw_state"


class FSMContextMiddleware(BaseMiddleware[MaxoUpdate[Any]]):
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

        storage_key = self.make_storage_key(
            bot_id=ctx["bot"].state.info.user_id,
            update_context=ctx[UPDATE_CONTEXT_KEY],
        )
        if storage_key is None:
            return await next(ctx)

        async with self._events_isolation.lock(key=storage_key):
            fsm_context = FSMContext(key=storage_key, storage=self._storage)
            ctx[FSM_CONTEXT_KEY] = fsm_context
            ctx[FSM_CONTEXT_STATE_KEY] = fsm_context
            ctx[RAW_STATE_KEY] = await fsm_context.get_state()

            return await next(ctx)

    def make_storage_key(
        self,
        bot_id: int,
        update_context: UpdateContext,
    ) -> StorageKey | None:
        chat_id, user_id = update_context.chat_id, update_context.user_id
        if chat_id is None or user_id is None:
            return None

        return StorageKey(bot_id=bot_id, chat_id=chat_id, user_id=user_id)
