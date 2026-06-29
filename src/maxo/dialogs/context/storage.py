from contextlib import AsyncExitStack
from copy import copy
from typing import Any

from maxo import Bot
from maxo.dialogs.api.entities import DEFAULT_STACK_ID, AccessSettings, Context, Stack
from maxo.dialogs.api.exceptions import UnknownIntent, UnknownState
from maxo.enums import ChatType
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import StorageKey
from maxo.fsm.storages.base import BaseEventIsolation, BaseStorage
from maxo.serialization import create_retort
from maxo.types import Attachments

retort = create_retort()


class StorageProxy:
    def __init__(
        self,
        storage: BaseStorage,
        events_isolation: BaseEventIsolation,
        user_id: int | None,
        chat_id: int | None,
        chat_type: ChatType | None,
        bot: Bot,
        state_groups: dict[str, type[StatesGroup]],
    ) -> None:
        self.storage = storage
        self.events_isolation = events_isolation
        self.state_groups = state_groups
        self.user_id = user_id
        self.chat_id = chat_id
        self.chat_type = chat_type
        self.bot = bot
        self.lock_stack = AsyncExitStack()

    async def lock(self, key: StorageKey) -> None:
        await self.lock_stack.enter_async_context(self.events_isolation.lock(key))

    async def unlock(self) -> None:
        await self.lock_stack.aclose()

    async def load_context(self, intent_id: str) -> Context:
        data = await self.storage.get_data(
            key=self._context_key(intent_id),
        )
        if not data:
            raise UnknownIntent(
                f"Context not found for intent id: {intent_id}",
            )
        data["access_settings"] = self._parse_access_settings(
            data.pop("access_settings", None),
        )
        data["state"] = self._state(data["state"])
        return Context(**data)

    def _default_access_settings(self, stack_id: str) -> AccessSettings:
        if stack_id == DEFAULT_STACK_ID and self.user_id:
            return AccessSettings(user_ids=[self.user_id])
        return AccessSettings(user_ids=[])

    async def load_stack(self, stack_id: str = DEFAULT_STACK_ID) -> Stack:
        fixed_stack_id = self._fixed_stack_id(stack_id)
        key = self._stack_key(fixed_stack_id)
        await self.lock(key)
        data = await self.storage.get_data(key)
        access_settings = self._default_access_settings(stack_id)
        if not data:
            return Stack(_id=fixed_stack_id, access_settings=access_settings)

        if "last_attachments" in data:
            data["last_attachments"] = retort.load(
                data["last_attachments"],
                list[Attachments],
            )

        return Stack(access_settings=access_settings, **data)

    async def save_context(self, context: Context | None) -> None:
        if not context:
            return
        data = copy(vars(context))
        data["state"] = data["state"].state
        data["access_settings"] = self._dump_access_settings(
            context.access_settings,
        )
        await self.storage.set_data(
            key=self._context_key(context.id),
            data=data,
        )

    async def remove_context(self, intent_id: str) -> None:
        await self.storage.set_data(
            key=self._context_key(intent_id),
            data={},
        )

    async def remove_stack(self, stack_id: str) -> None:
        await self.storage.set_data(
            key=self._stack_key(stack_id),
            data={},
        )

    async def save_stack(self, stack: Stack | None) -> None:
        if not stack:
            return
        if stack.empty() and not stack.last_message_id:
            await self.storage.set_data(
                key=self._stack_key(stack.id),
                data={},
            )
        else:
            data = {
                "_id": stack.id,
                "intents": stack.intents,
                "last_message_id": stack.last_message_id,
                "last_sequence_id": stack.last_sequence_id,
                "last_attachments": retort.dump(
                    stack.last_attachments,
                    list[Attachments],
                ),
            }
            await self.storage.set_data(
                key=self._stack_key(stack.id),
                data=data,
            )

    def _context_key(self, intent_id: str) -> StorageKey:
        return StorageKey(
            bot_id=self.bot.state.info.user_id,
            chat_id=self.chat_id,
            user_id=self.chat_id,  # Неожиданно, но это нужно для работы в группах
            destiny=f"aiogd:context:{intent_id}",
        )

    def _fixed_stack_id(self, stack_id: str) -> str:
        if stack_id != DEFAULT_STACK_ID:
            return stack_id
        if self.chat_type == ChatType.DIALOG:
            return stack_id
        return f"<{self.user_id}>"

    def _stack_key(self, stack_id: str) -> StorageKey:
        stack_id = self._fixed_stack_id(stack_id)
        return StorageKey(
            bot_id=self.bot.state.info.user_id,
            chat_id=self.chat_id,
            user_id=self.chat_id,  # Неожиданно, но это нужно для работы в группах
            destiny=f"aiogd:stack:{stack_id}",
        )

    def _state(self, state: str) -> State:
        group, *_ = state.partition(":")
        try:
            for real_state in self.state_groups[group].__states__:
                if real_state.state == state:
                    return real_state
        except KeyError:
            raise UnknownState(f"Unknown state group {group}") from None
        raise UnknownState(f"Unknown state {state}")

    def _parse_access_settings(
        self,
        raw: dict[Any, Any] | None,
    ) -> AccessSettings | None:
        if not raw:
            return None
        return AccessSettings(
            user_ids=raw.get("user_ids") or [],
            custom=raw.get("custom"),
        )

    def _dump_access_settings(
        self,
        access_settings: AccessSettings | None,
    ) -> dict[Any, Any] | None:
        if not access_settings:
            return None
        return {
            "user_ids": access_settings.user_ids,
            "custom": access_settings.custom,
        }
