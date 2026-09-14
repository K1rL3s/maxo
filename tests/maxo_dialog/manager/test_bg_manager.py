import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import Dispatcher
from maxo.dialogs.api.entities import (
    DEFAULT_STACK_ID,
    DialogAction,
    DialogStartEvent,
    DialogSwitchEvent,
    DialogUpdateEvent,
    ShowMode,
    StartMode,
)
from maxo.dialogs.api.internal import FakeUser
from maxo.dialogs.manager.bg_manager import BgManager, BgManagerFactoryImpl
from maxo.dialogs.manager.updater import Updater
from maxo.enums import ChatType
from maxo.fsm import State, StatesGroup
from maxo.types import Chat, ChatMembersList, User
from tests.constants import NOW


class SG(StatesGroup):
    first = State()


def real_user(user_id: int = 7) -> User:
    return User(
        user_id=user_id,
        is_bot=False,
        first_name="Real",
        last_activity_time=NOW,
    )


def fake_user(user_id: int = 7) -> FakeUser:
    return FakeUser(
        user_id=user_id,
        is_bot=False,
        first_name="",
        last_activity_time=NOW,
    )


def make_bot() -> MagicMock:
    bot = MagicMock()
    loaded = real_user()
    chat = MagicMock(spec=Chat)
    chat.unsafe_dialog_with_user = loaded
    bot.get_chat = AsyncMock(return_value=chat)
    members = MagicMock(spec=ChatMembersList)
    members.members = [loaded]
    bot.get_members = AsyncMock(return_value=members)
    return bot


def make_manager(
    *,
    user: User | None = None,
    chat_id: int | None = 1,
    chat_type: ChatType = ChatType.CHAT,
    load: bool = False,
    bot: Any = None,
    stack_id: str | None = "stack",
    intent_id: str | None = "intent",
) -> BgManager:
    manager = BgManager(
        user=user or fake_user(),
        chat_id=chat_id,
        bot=bot or make_bot(),
        dp=Dispatcher(),
        intent_id=intent_id,
        stack_id=stack_id,
        load=load,
        chat_type=chat_type,
    )
    manager._updater = MagicMock(spec=Updater)
    manager._updater.notify = AsyncMock()
    return manager


class TestGetFakeUser:
    def test_returns_current_user_without_id(self) -> None:
        user = fake_user()
        manager = make_manager(user=user)

        assert manager._get_fake_user() is user

    def test_returns_current_user_for_same_id(self) -> None:
        user = fake_user(7)
        manager = make_manager(user=user)

        assert manager._get_fake_user(7) is user

    def test_builds_fake_user_for_other_id(self) -> None:
        manager = make_manager(user=fake_user(7))

        other = manager._get_fake_user(99)

        assert isinstance(other, FakeUser)
        assert other.id == 99


class TestBg:
    def test_keeps_stack_and_intent_for_same_context(self) -> None:
        child = make_manager().bg()

        assert isinstance(child, BgManager)
        assert child.stack_id == "stack"
        assert child.intent_id == "intent"
        assert child._event_context.chat_id == 1

    def test_resets_stack_for_other_context(self) -> None:
        child = make_manager().bg(user_id=99, chat_id=2)

        assert isinstance(child, BgManager)
        assert child.stack_id == DEFAULT_STACK_ID
        assert child.intent_id is None

    def test_explicit_stack_id_drops_intent(self) -> None:
        child = make_manager().bg(stack_id="other")

        assert isinstance(child, BgManager)
        assert child.stack_id == "other"
        assert child.intent_id is None


class TestLoad:
    async def test_does_nothing_when_load_disabled(self) -> None:
        bot = make_bot()
        await make_manager(bot=bot, load=False)._load()

        bot.get_chat.assert_not_awaited()
        bot.get_members.assert_not_awaited()

    async def test_does_nothing_for_already_loaded_user(self) -> None:
        bot = make_bot()
        await make_manager(bot=bot, load=True, user=real_user())._load()

        bot.get_chat.assert_not_awaited()
        bot.get_members.assert_not_awaited()

    async def test_skips_when_chat_id_unknown(self) -> None:
        bot = make_bot()
        await make_manager(bot=bot, load=True, chat_id=None)._load()

        bot.get_chat.assert_not_awaited()
        bot.get_members.assert_not_awaited()

    async def test_loads_user_from_dialog(self) -> None:
        bot = make_bot()
        manager = make_manager(bot=bot, load=True, chat_type=ChatType.DIALOG)

        await manager._load()

        bot.get_chat.assert_awaited_once_with(chat_id=1)
        assert manager._event_context.chat is not None
        assert manager._event_context.user is not None
        assert manager._event_context.user.first_name == "Real"

    async def test_loads_user_from_chat_members(self) -> None:
        bot = make_bot()
        manager = make_manager(bot=bot, load=True, chat_type=ChatType.CHAT)

        await manager._load()

        bot.get_members.assert_awaited_once_with(chat_id=1, user_ids=[7])
        assert manager._event_context.user is not None
        assert manager._event_context.user.first_name == "Real"

    async def test_keeps_fake_user_when_no_members_found(self) -> None:
        bot = make_bot()
        bot.get_members.return_value.members = []
        manager = make_manager(bot=bot, load=True)

        await manager._load()

        assert isinstance(manager._event_context.user, FakeUser)


class TestNotifications:
    def sent_event(self, manager: BgManager) -> Any:
        updater = cast(MagicMock, manager._updater)
        updater.notify.assert_awaited_once()
        return updater.notify.call_args.kwargs["update"]

    async def test_done(self) -> None:
        manager = make_manager()

        await manager.done(result={"a": 1}, show_mode=ShowMode.EDIT)

        event = self.sent_event(manager)
        assert isinstance(event, DialogUpdateEvent)
        assert event.action is DialogAction.DONE
        assert event.data == {"a": 1}
        assert event.show_mode is ShowMode.EDIT

    async def test_start(self) -> None:
        manager = make_manager()

        await manager.start(SG.first, data={"x": 1}, mode=StartMode.RESET_STACK)

        event = self.sent_event(manager)
        assert isinstance(event, DialogStartEvent)
        assert event.new_state == SG.first
        assert event.mode is StartMode.RESET_STACK

    async def test_switch_to(self) -> None:
        manager = make_manager()

        await manager.switch_to(SG.first)

        event = self.sent_event(manager)
        assert isinstance(event, DialogSwitchEvent)
        assert event.new_state == SG.first

    async def test_update_without_data(self) -> None:
        manager = make_manager()

        await manager.update()

        event = self.sent_event(manager)
        assert event.action is DialogAction.UPDATE
        assert event.data == {}

    async def test_update_with_data(self) -> None:
        manager = make_manager()

        await manager.update({"k": "v"})

        assert self.sent_event(manager).data == {"k": "v"}


class TestForeground:
    async def test_fg_yields_manager_and_completes(self) -> None:
        manager = make_manager()
        inner = MagicMock()

        def notify_task(bot: Any, update: Any) -> Any:
            update.entered.set_result(inner)
            return asyncio.sleep(0)

        manager._updater.notify_task = MagicMock(side_effect=notify_task)  # type: ignore[method-assign]

        async with manager.fg() as fg_manager:
            assert fg_manager is inner

    async def test_fg_propagates_exception(self) -> None:
        manager = make_manager()
        events: list[Any] = []

        def notify_task(bot: Any, update: Any) -> Any:
            events.append(update)
            update.entered.set_result(MagicMock())
            return asyncio.sleep(0)

        manager._updater.notify_task = MagicMock(side_effect=notify_task)  # type: ignore[method-assign]

        with pytest.raises(RuntimeError, match="boom"):
            async with manager.fg():
                raise RuntimeError("boom")

        assert events[0].exited.exception() is not None


class TestFactory:
    def test_builds_bg_manager(self) -> None:
        factory = BgManagerFactoryImpl(Dispatcher())

        manager = factory.bg(
            bot=MagicMock(),
            user_id=5,
            chat_id=6,
            chat_type=ChatType.DIALOG,
        )

        assert isinstance(manager, BgManager)
        assert manager.stack_id == DEFAULT_STACK_ID
        assert manager._event_context.chat_id == 6

    def test_keeps_explicit_stack_id(self) -> None:
        factory = BgManagerFactoryImpl(Dispatcher())

        manager = factory.bg(bot=MagicMock(), user_id=5, chat_id=6, stack_id="s")

        assert isinstance(manager, BgManager)
        assert manager.stack_id == "s"
