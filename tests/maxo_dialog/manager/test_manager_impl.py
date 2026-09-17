from collections.abc import Awaitable, Callable
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import Dispatcher
from maxo.dialogs.api.entities import (
    DEFAULT_STACK_ID,
    EVENT_CONTEXT_KEY,
    Context,
    EventContext,
    LaunchMode,
    MediaAttachment,
    MediaId,
    NewMessage,
    OldMessage,
    ShowMode,
    Stack,
    StartMode,
)
from maxo.dialogs.api.exceptions import (
    IncorrectBackgroundError,
    InvalidKeyboardType,
    NoContextError,
)
from maxo.dialogs.api.internal import CONTEXT_KEY, STACK_KEY, STORAGE_KEY, FakeUser
from maxo.dialogs.api.protocols import MessageNotModified
from maxo.dialogs.manager.bg_manager import BgManager
from maxo.dialogs.manager.manager import ManagerImpl
from maxo.enums import AttachmentType, ChatType
from maxo.fsm import State, StatesGroup
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.routing.signals import MaxoUpdate
from maxo.types import (
    Callback,
    CallbackButton,
    ErrorEvent,
    Message,
    MessageBody,
    MessageButton,
    MessageCallback,
    MessageCreated,
    Recipient,
    UpdateContext,
)
from tests.constants import NOW
from tests.maxo_dialog.conftest import make_message_created, make_user


class SG(StatesGroup):
    first = State()
    second = State()


class Other(StatesGroup):
    only = State()


def make_callback(with_message: bool = True) -> MessageCallback:
    kwargs: dict[str, Any] = {}
    if with_message:
        kwargs["message"] = Message(
            timestamp=NOW,
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
            body=MessageBody(mid="m", seq=1),
        )
    return MessageCallback(
        timestamp=NOW,
        callback=Callback(
            callback_id="c",
            user=make_user(),
            timestamp=NOW,
            payload="p",
        ),
        **kwargs,
    )


def make_context(state: State = SG.first) -> Context:
    return Context(
        _intent_id="intent",
        _stack_id=DEFAULT_STACK_ID,
        state=state,
        start_data={"s": 1},
        widget_data={},
        dialog_data={"d": 1},
    )


def make_manager(
    *,
    event: Any = None,
    state: State | None = SG.first,
    stack: Stack | None = None,
    getter: Any = None,
    chat_type: ChatType = ChatType.DIALOG,
) -> ManagerImpl:
    stack = stack if stack is not None else Stack(_id=DEFAULT_STACK_ID)
    real_context = make_context(state) if state is not None else None
    ctx: dict[Any, Any] = {
        "bot": MagicMock(),
        STACK_KEY: stack,
        CONTEXT_KEY: real_context,
        STORAGE_KEY: MagicMock(
            remove_context=AsyncMock(),
            save_stack=AsyncMock(),
        ),
        UPDATE_CONTEXT_KEY: UpdateContext(chat_id=10, user_id=1, type=chat_type),
        EVENT_CONTEXT_KEY: EventContext(
            bot=MagicMock(),
            chat=None,
            chat_id=10,
            chat_type=chat_type,
            user=make_user(),
            user_id=1,
        ),
    }
    return ManagerImpl(
        event=event if event is not None else make_message_created(),
        message_manager=MagicMock(
            remove_kbd=AsyncMock(),
            answer_callback=AsyncMock(),
            show_message=AsyncMock(),
        ),
        media_id_storage=MagicMock(),
        registry=MagicMock(),
        router=Dispatcher(),
        ctx=ctx,  # type: ignore[arg-type]
        getter=getter,
    )


def make_new_message() -> NewMessage:
    return NewMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
        text="t",
    )


def registry(manager: ManagerImpl) -> MagicMock:
    # _registry типизирован как Protocol, в этих тестах используется MagicMock
    return cast(MagicMock, manager._registry)


def message_manager(manager: ManagerImpl) -> MagicMock:
    # message_manager типизирован как Protocol, в этих тестах используется MagicMock
    return cast(MagicMock, manager.message_manager)


class TestContextAccess:
    def test_dialog_and_start_data(self) -> None:
        manager = make_manager()

        assert manager.dialog_data == {"d": 1}
        assert manager.start_data == {"s": 1}

    def test_check_disabled(self) -> None:
        manager = make_manager()
        manager.disabled = True

        with pytest.raises(IncorrectBackgroundError):
            manager.check_disabled()

    def test_current_context_without_context(self) -> None:
        manager = make_manager(state=None)

        with pytest.raises(NoContextError):
            manager.current_context()

    def test_has_context(self) -> None:
        assert make_manager().has_context() is True
        assert make_manager(state=None).has_context() is False

    def test_is_preview_is_false(self) -> None:
        assert make_manager().is_preview() is False

    def test_middleware_data_and_event(self) -> None:
        event = make_message_created()
        manager = make_manager(event=event)

        assert manager.middleware_data[UPDATE_CONTEXT_KEY] == UpdateContext(
            chat_id=10,
            user_id=1,
            type=ChatType.DIALOG,
        )
        assert manager.event is event

    async def test_load_data_without_getter(self) -> None:
        data = await make_manager().load_data()

        assert data["dialog_data"] == {"d": 1}
        assert data["start_data"] == {"s": 1}

    async def test_load_data_with_getter(self) -> None:
        getter = AsyncMock(return_value={"extra": 1})

        data = await make_manager(getter=getter).load_data()

        assert data["extra"] == 1

    async def test_close_manager_disables(self) -> None:
        manager = make_manager()

        await manager.close_manager()

        assert manager.disabled is True

    async def test_fg_returns_self(self) -> None:
        manager = make_manager()

        async with manager.fg() as fg:
            assert fg is manager


class TestNavigation:
    async def test_next(self) -> None:
        manager = make_manager()
        registry(manager).find_dialog.return_value = MagicMock(
            states=MagicMock(return_value=[SG.first, SG.second]),
        )
        manager.show = AsyncMock()  # type: ignore[method-assign]

        await manager.next()

        assert manager.current_context().state == SG.second

    async def test_next_beyond_last(self) -> None:
        manager = make_manager(state=SG.second)
        registry(manager).find_dialog.return_value = MagicMock(
            states=MagicMock(return_value=[SG.first, SG.second]),
        )

        with pytest.raises(ValueError, match="non-existent state"):
            await manager.next()

    async def test_back(self) -> None:
        manager = make_manager(state=SG.second)
        registry(manager).find_dialog.return_value = MagicMock(
            states=MagicMock(return_value=[SG.first, SG.second]),
        )
        manager.show = AsyncMock()  # type: ignore[method-assign]

        await manager.back()

        assert manager.current_context().state == SG.first

    async def test_back_before_first(self) -> None:
        manager = make_manager()
        registry(manager).find_dialog.return_value = MagicMock(
            states=MagicMock(return_value=[SG.first, SG.second]),
        )

        with pytest.raises(ValueError, match="non-existent state"):
            await manager.back()

    async def test_switch_to_other_group_rejected(self) -> None:
        manager = make_manager()

        with pytest.raises(ValueError, match="another state group"):
            await manager.switch_to(Other.only)

    async def test_switch_to_sets_state_and_show_mode(self) -> None:
        manager = make_manager()

        await manager.switch_to(SG.second, ShowMode.EDIT)

        assert manager.current_context().state == SG.second
        assert manager.show_mode is ShowMode.EDIT


class TestStartModes:
    async def test_unknown_start_mode(self) -> None:
        manager = make_manager()

        with pytest.raises(ValueError, match="Unknown start mode"):
            await manager.start(SG.first, mode="nope")  # type: ignore[arg-type]

    async def test_reset_stack_clears_contexts(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID)
        stack.push(SG.first, {})
        manager = make_manager(stack=stack)

        await manager.reset_stack(remove_keyboard=False)

        assert stack.empty()
        assert manager._ctx[CONTEXT_KEY] is None

    async def test_reset_stack_removes_keyboard(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID, last_message_id="1")
        manager = make_manager(stack=stack)

        await manager.reset_stack(remove_keyboard=True)

        message_manager(manager).remove_kbd.assert_awaited_once()


class TestLaunchMode:
    async def test_exclusive_resets_stack(self) -> None:
        manager = make_manager()
        manager.reset_stack = AsyncMock()  # type: ignore[method-assign]

        await manager._process_launch_mode(
            None,
            MagicMock(launch_mode=LaunchMode.EXCLUSIVE),
        )

        manager.reset_stack.assert_awaited_once()

    async def test_single_top_pops_same_dialog(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID)
        stack.push(SG.first, {})
        manager = make_manager(stack=stack)
        dialog = MagicMock(launch_mode=LaunchMode.SINGLE_TOP)

        await manager._process_launch_mode(dialog, dialog)

        assert stack.empty()
        assert manager._ctx[CONTEXT_KEY] is None

    async def test_standard_does_nothing(self) -> None:
        manager = make_manager()
        manager.reset_stack = AsyncMock()  # type: ignore[method-assign]

        await manager._process_launch_mode(
            None,
            MagicMock(launch_mode=LaunchMode.STANDARD),
        )

        manager.reset_stack.assert_not_awaited()


class TestKeyboardCompatibility:
    def new_message(self, keyboard: Any) -> NewMessage:
        return NewMessage(
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
            text="t",
            keyboard=keyboard,
        )

    def test_default_stack_allows_message_button(self) -> None:
        manager = make_manager()
        message = self.new_message([[MessageButton(text="b")]])

        manager._ensure_stack_compatible(manager.current_stack(), message)

    def test_non_default_stack_rejects_message_button(self) -> None:
        stack = Stack(_id="other")
        manager = make_manager(stack=stack)
        message = self.new_message([[MessageButton(text="b")]])

        with pytest.raises(InvalidKeyboardType):
            manager._ensure_stack_compatible(stack, message)

    def test_non_default_stack_allows_callback_button(self) -> None:
        stack = Stack(_id="other")
        manager = make_manager(stack=stack)
        message = self.new_message([[CallbackButton(text="b", payload="p")]])

        manager._ensure_stack_compatible(stack, message)


class TestAnswerCallback:
    async def test_ignores_non_callback_event(self) -> None:
        manager = make_manager()

        await manager.answer_callback()
        message_manager(manager).answer_callback.assert_not_awaited()

    async def test_ignores_simulated_event(self) -> None:
        manager = make_manager(event=make_callback())
        manager.is_event_simulated = MagicMock(return_value=True)  # type: ignore[method-assign]

        await manager.answer_callback()
        message_manager(manager).answer_callback.assert_not_awaited()

    async def test_answers_real_callback(self) -> None:
        manager = make_manager(event=make_callback())

        await manager.answer_callback()

        message_manager(manager).answer_callback.assert_awaited_once()


class TestShow:
    async def test_no_update_skips_rendering(self) -> None:
        manager = make_manager()
        manager.show_mode = ShowMode.NO_UPDATE

        await manager.show()

        message_manager(manager).show_message.assert_not_awaited()

    async def test_remove_kbd_skipped_without_last_message(self) -> None:
        manager = make_manager()

        await manager._remove_kbd()

        message_manager(manager).remove_kbd.assert_not_awaited()


class TestCalcShowMode:
    def test_explicit_mode_wins(self) -> None:
        manager = make_manager()
        manager.show_mode = ShowMode.DELETE_AND_SEND

        assert manager._calc_show_mode() is ShowMode.DELETE_AND_SEND

    def test_non_dialog_chat_edits(self) -> None:
        assert make_manager(chat_type=ChatType.CHAT)._calc_show_mode() is ShowMode.EDIT

    def test_non_default_stack_edits(self) -> None:
        manager = make_manager(stack=Stack(_id="other"))

        assert manager._calc_show_mode() is ShowMode.EDIT

    def test_message_created_sends(self) -> None:
        assert make_manager()._calc_show_mode() is ShowMode.SEND

    def test_callback_edits(self) -> None:
        assert make_manager(event=make_callback())._calc_show_mode() is ShowMode.EDIT


class TestLastMessage:
    def test_save_and_restore_last_message(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID)
        manager = make_manager(stack=stack, event=make_callback())
        message = OldMessage(
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=10, user_id=1),
            message_id="55",
            sequence_id=55,
            text="t",
            attachments=[],
        )

        manager._save_last_message(message)

        assert stack.last_message_id == "55"
        assert stack.last_sequence_id == 55


class TestBackground:
    def test_bg_keeps_current_stack_and_intent(self) -> None:
        manager = make_manager(stack=Stack(_id="other"))

        child = manager.bg()

        assert isinstance(child, BgManager)
        assert child.stack_id == "other"
        assert child.intent_id == "intent"

    def test_bg_for_other_chat_resets_stack(self) -> None:
        manager = make_manager(stack=Stack(_id="other"))

        child = manager.bg(chat_id=99)

        assert isinstance(child, BgManager)
        assert child.stack_id == DEFAULT_STACK_ID
        assert child.intent_id is None

    def test_bg_for_other_user_resets_stack(self) -> None:
        manager = make_manager(stack=Stack(_id="other"))

        child = manager.bg(user_id=2)

        assert isinstance(child, BgManager)
        assert child.stack_id == DEFAULT_STACK_ID
        assert child.intent_id is None

    def test_get_fake_user_for_other_id(self) -> None:
        user = make_manager().bg(user_id=42)

        assert isinstance(user, BgManager)

    def test_get_fake_user_takes_user_from_event_context(self) -> None:
        manager = make_manager(event=make_callback(with_message=False))
        event_context: EventContext = manager.middleware_data[EVENT_CONTEXT_KEY]

        assert manager._get_fake_user() is event_context.user

    def test_get_fake_user_for_event_without_user(self) -> None:
        channel_post = MessageCreated(
            timestamp=NOW,
            message=Message(
                timestamp=NOW,
                recipient=Recipient(chat_type=ChatType.CHANNEL, chat_id=10),
                body=MessageBody(mid="m", seq=1, text="post"),
            ),
        )
        manager = make_manager(event=channel_post, chat_type=ChatType.CHANNEL)
        event_context: EventContext = manager.middleware_data[EVENT_CONTEXT_KEY]
        event_context.user = None
        event_context.user_id = None

        user = manager._get_fake_user(42)

        assert isinstance(user, FakeUser)
        assert user.id == 42

    def test_get_fake_chat_requires_chat_id_without_update_context(self) -> None:
        manager = make_manager()
        del manager._ctx[UPDATE_CONTEXT_KEY]

        with pytest.raises(ValueError, match="Explicit `chat_id` is required"):
            manager._get_fake_chat()

    def test_get_fake_chat_for_explicit_id(self) -> None:
        manager = make_manager()

        chat = manager._get_fake_chat(99)

        assert chat.id == 99


class TestUpdate:
    async def test_update_merges_dialog_data(self) -> None:
        manager = make_manager()
        manager.show = AsyncMock()  # type: ignore[method-assign]

        await manager.update({"new": 2})

        assert manager.current_context().dialog_data == {"d": 1, "new": 2}
        manager.show.assert_awaited_once()

    async def test_update_without_data(self) -> None:
        manager = make_manager()
        manager.show = AsyncMock()  # type: ignore[method-assign]

        await manager.update()

        assert manager.current_context().dialog_data == {"d": 1}


class TestFind:
    def test_find_missing_widget(self) -> None:
        manager = make_manager()
        registry(manager).find_dialog.return_value = MagicMock(
            find=MagicMock(return_value=None),
        )

        assert manager.find("nope") is None

    def test_find_returns_managed_widget(self) -> None:
        manager = make_manager()
        managed = MagicMock()
        widget = MagicMock(managed=MagicMock(return_value=managed))
        registry(manager).find_dialog.return_value = MagicMock(
            find=MagicMock(return_value=widget),
        )

        assert manager.find("btn") is managed


def test_start_mode_enum_covers_new_stack() -> None:
    assert StartMode.NEW_STACK in StartMode


class TestStartNewStack:
    async def test_new_stack_delegates_to_bg(self) -> None:
        manager = make_manager()
        bg = MagicMock(start=AsyncMock())
        manager.bg = MagicMock(return_value=bg)  # type: ignore[method-assign]

        await manager.start(SG.first, mode=StartMode.NEW_STACK)

        bg.start.assert_awaited_once()

    async def test_reset_stack_mode(self) -> None:
        manager = make_manager()
        manager.reset_stack = AsyncMock()  # type: ignore[method-assign]
        manager._start_normal = AsyncMock()  # type: ignore[method-assign]

        await manager.start(SG.first, mode=StartMode.RESET_STACK)

        manager.reset_stack.assert_awaited_once()
        manager._start_normal.assert_awaited_once()


class TestStartNormal:
    async def test_rejects_start_on_top_of_exclusive(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID)
        stack.push(SG.first, {})
        manager = make_manager(stack=stack)
        registry(manager).find_dialog.return_value = MagicMock(
            launch_mode=LaunchMode.EXCLUSIVE,
        )

        with pytest.raises(ValueError, match="launch_mode"):
            await manager._start_normal(SG.first, None, None)


class TestShowErrors:
    async def test_message_not_modified_skips_saving(self) -> None:
        manager = make_manager()
        registry(manager).find_dialog.return_value = MagicMock(
            render=AsyncMock(return_value=make_new_message()),
        )
        message_manager(manager).show_message = AsyncMock(
            side_effect=MessageNotModified,
        )
        manager._save_last_message = MagicMock()  # type: ignore[method-assign]

        await manager.show()

        manager._save_last_message.assert_not_called()

    async def test_render_error_gets_state_note(self) -> None:
        manager = make_manager()
        registry(manager).find_dialog.return_value = MagicMock(
            render=AsyncMock(side_effect=RuntimeError("boom")),
        )

        with pytest.raises(RuntimeError) as info:
            await manager.show()

        assert any("maxo.dialogs state" in note for note in info.value.__notes__)


class TestLoadCachedMedia:
    async def test_fills_media_id_from_storage(self) -> None:
        manager = make_manager()
        attachment = MediaAttachment(
            type=AttachmentType.IMAGE,
            url="http://e.com/a.png",
        )
        new_message = make_new_message()
        new_message.media = [attachment]
        # media_id_storage типизирован как Protocol,
        # в этих тестах используется MagicMock
        cast(MagicMock, manager.media_id_storage).get_media_id = AsyncMock(
            return_value=MediaId(token="tok"),  # noqa: S106
        )

        await manager._load_cached_media(new_message)

        assert attachment.media_id is not None

    async def test_skips_attachment_with_media_id(self) -> None:
        manager = make_manager()
        attachment = MediaAttachment(
            type=AttachmentType.IMAGE,
            media_id=MediaId(token="tok"),  # noqa: S106
        )
        new_message = make_new_message()
        new_message.media = [attachment]
        # media_id_storage типизирован как Protocol,
        # в этих тестах используется MagicMock
        storage = cast(MagicMock, manager.media_id_storage)
        storage.get_media_id = AsyncMock()

        await manager._load_cached_media(new_message)

        storage.get_media_id.assert_not_awaited()


class TestGetLastMessage:
    def test_restores_from_stack_for_callback(self) -> None:
        stack = Stack(_id=DEFAULT_STACK_ID, last_message_id="55", last_sequence_id=55)
        manager = make_manager(stack=stack, event=make_callback(with_message=False))

        old_message = manager._get_last_message()

        assert old_message is not None
        assert old_message.message_id == "55"

    def test_returns_none_without_last_message(self) -> None:
        manager = make_manager(event=make_callback(with_message=False))

        assert manager._get_last_message() is None

    def test_unwraps_error_event(self) -> None:
        inner = make_callback(with_message=False)
        error_event: ErrorEvent[RuntimeError, MessageCallback] = ErrorEvent(
            exception=RuntimeError("x"),
            update=MaxoUpdate(update=inner),
        )
        manager = make_manager(event=error_event)

        assert manager._get_last_message() is None


class TestClosedManager:
    @pytest.mark.parametrize(
        "call",
        [
            pytest.param(lambda m: m.next(), id="next"),
            pytest.param(lambda m: m.back(), id="back"),
            pytest.param(lambda m: m.update(), id="update"),
            pytest.param(lambda m: m.show(), id="show"),
            pytest.param(lambda m: m.answer_callback(), id="answer_callback"),
        ],
    )
    async def test_raises_background_error(
        self,
        call: Callable[[ManagerImpl], Awaitable[None]],
    ) -> None:
        manager = make_manager(event=make_callback())
        await manager.close_manager()

        with pytest.raises(IncorrectBackgroundError) as info:
            await call(manager)

        assert info.value.__context__ is None
