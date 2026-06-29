import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from maxo import Bot, Dispatcher, loggers
from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import (
    DEFAULT_STACK_ID,
    AccessSettings,
    Data,
    DialogAction,
    DialogStartEvent,
    DialogSwitchEvent,
    DialogUpdateEvent,
    EventContext,
    ShowMode,
    StartMode,
)
from maxo.dialogs.api.entities.update_event import DialogFgEvent
from maxo.dialogs.api.internal import FakeUser
from maxo.dialogs.api.protocols import BaseDialogManager, BgManagerFactory
from maxo.dialogs.manager.updater import Updater
from maxo.dialogs.utils import is_user_loaded
from maxo.enums import ChatType
from maxo.fsm import State
from maxo.types import Chat, ChatMembersList, Recipient, User


class BgManager(BaseDialogManager):
    def __init__(
        self,
        user: User,
        chat_id: int | None,
        bot: Bot,
        dp: Dispatcher,
        intent_id: str | None,
        stack_id: str | None,
        load: bool = False,
        chat_type: ChatType = ChatType.CHAT,
    ) -> None:
        self._event_context = EventContext(
            chat_id=chat_id,
            user_id=user.id,
            chat_type=chat_type,
            user=user,
            chat=None,
            bot=bot,
        )
        self._router = dp
        self._updater = Updater(dp)
        self.intent_id = intent_id
        self.stack_id = stack_id
        self.load = load

    def _get_fake_user(self, user_id: int | None = None) -> User:
        if self._event_context.user is not None and (
            user_id is None or user_id == self._event_context.user.id
        ):
            return self._event_context.user
        return FakeUser(
            user_id=user_id,
            is_bot=False,
            first_name="",
            last_activity_time=datetime.now(UTC),
        )

    def bg(
        self,
        user_id: int | None = None,
        chat_id: int | None = None,
        stack_id: str | None = None,
        load: bool = False,
    ) -> "BaseDialogManager":
        user = self._get_fake_user(user_id)

        new_event_context = EventContext(
            bot=self._event_context.bot,
            user=user,
            chat_id=chat_id,
            user_id=user_id,
            chat_type=self._event_context.chat_type,
            chat=None,
        )
        if stack_id is None:
            if self._event_context == new_event_context:
                stack_id = self.stack_id
                intent_id = self.intent_id
            else:
                stack_id = DEFAULT_STACK_ID
                intent_id = None
        else:
            intent_id = None

        return BgManager(
            user=new_event_context.user,
            chat_id=new_event_context.chat_id,
            bot=new_event_context.bot,
            dp=self._router,
            intent_id=intent_id,
            stack_id=stack_id,
            load=load,
            chat_type=new_event_context.chat_type,
        )

    def _base_event_params(self) -> dict[str, Any]:
        return {
            "user": self._event_context.user,
            "recipient": Recipient(
                user_id=self._event_context.user.id,
                chat_id=self._event_context.chat_id,
                chat_type=self._event_context.chat_type,
            ),
            "bot": self._event_context.bot,
            "intent_id": self.intent_id,
            "stack_id": self.stack_id,
        }

    async def _notify(self, event: DialogUpdateEvent) -> None:
        bot = self._event_context.bot
        await self._updater.notify(bot=bot, update=event)

    async def _load(self) -> None:
        if not self.load:
            return

        bot = self._event_context.bot
        if not is_user_loaded(self._event_context.user):
            loggers.dialogs.debug(
                "load user %s from chat %s",
                self._event_context.user_id,
                self._event_context.chat_id,
            )
            if self._event_context.chat_type == ChatType.DIALOG:
                chat: Chat = await bot.get_chat(chat_id=self._event_context.chat_id)
                self._event_context.chat = chat
                self._event_context.user = chat.unsafe_dialog_with_user
            else:
                chat_members: ChatMembersList = await bot.get_members(
                    chat_id=self._event_context.chat_id,
                    user_ids=[self._event_context.user_id],
                )
                if chat_members.members:
                    self._event_context.user = chat_members.members[0]

    async def done(
        self,
        result: Any = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        await self._load()
        await self._notify(
            DialogUpdateEvent(
                action=DialogAction.DONE,
                data=result,
                show_mode=show_mode,
                **self._base_event_params(),
            ),
        )

    async def start(
        self,
        state: State,
        data: Data = None,
        mode: StartMode = StartMode.NORMAL,
        show_mode: ShowMode | None = None,
        access_settings: AccessSettings | None = None,
    ) -> None:
        await self._load()
        await self._notify(
            DialogStartEvent(
                action=DialogAction.START,
                data=data,
                new_state=state,
                mode=mode,
                show_mode=show_mode,
                access_settings=access_settings,
                **self._base_event_params(),
            ),
        )

    async def switch_to(
        self,
        state: State,
        show_mode: ShowMode | None = None,
    ) -> None:
        await self._load()
        await self._notify(
            DialogSwitchEvent(
                action=DialogAction.SWITCH,
                data={},
                new_state=state,
                show_mode=show_mode,
                **self._base_event_params(),
            ),
        )

    async def update(
        self,
        data: dict | None = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        await self._load()
        await self._notify(
            DialogUpdateEvent(
                action=DialogAction.UPDATE,
                data=data or {},
                show_mode=show_mode,
                **self._base_event_params(),
            ),
        )

    @asynccontextmanager
    async def fg(self) -> AsyncIterator[DialogManager]:
        event = DialogFgEvent(
            data=None,
            action=DialogAction.FG,
            entered=asyncio.get_running_loop().create_future(),
            exited=asyncio.get_running_loop().create_future(),
            **self._base_event_params(),
        )
        bot = self._event_context.bot
        task = self._updater.notify_task(bot=bot, update=event)
        try:
            manager = await event.entered
            yield manager
        except Exception as e:
            event.exited.set_exception(e)
            raise
        else:
            event.exited.set_result(None)
        finally:
            await task


class BgManagerFactoryImpl(BgManagerFactory):
    def __init__(self, router: Dispatcher) -> None:
        self._dp = router

    def bg(
        self,
        bot: Bot,
        user_id: int,
        chat_id: int,
        stack_id: str | None = None,
        load: bool = False,
        chat_type: ChatType = ChatType.CHAT,
    ) -> "BaseDialogManager":
        user = FakeUser(
            user_id=user_id,
            is_bot=False,
            first_name="",
            last_activity_time=datetime.now(UTC),
        )
        if stack_id is None:
            stack_id = DEFAULT_STACK_ID

        return BgManager(
            user=user,
            chat_id=chat_id,
            bot=bot,
            dp=self._dp,
            intent_id=None,
            stack_id=stack_id,
            load=load,
            chat_type=chat_type,
        )
