import itertools
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, cast

from maxo import Ctx, loggers
from maxo.dialogs.api.entities import (
    DEFAULT_STACK_ID,
    EVENT_CONTEXT_KEY,
    AccessSettings,
    ChatEvent,
    Context,
    Data,
    EventContext,
    LaunchMode,
    NewMessage,
    OldMessage,
    ShowMode,
    Stack,
    StartMode,
    UnknownText,
)
from maxo.dialogs.api.exceptions import (
    IncorrectBackgroundError,
    InvalidKeyboardType,
    NoContextError,
)
from maxo.dialogs.api.internal import (
    CONTEXT_KEY,
    EVENT_SIMULATED,
    STACK_KEY,
    STORAGE_KEY,
    DataGetter,
    FakeUser,
    Widget,
)
from maxo.dialogs.api.internal.fake_data import FakeChat
from maxo.dialogs.api.protocols import (
    BaseDialogManager,
    DialogManager,
    DialogProtocol,
    DialogRegistryProtocol,
    MediaIdStorageProtocol,
    MessageManagerProtocol,
    MessageNotModified,
)
from maxo.dialogs.context.storage import StorageProxy
from maxo.dialogs.manager.bg_manager import BgManager
from maxo.enums import ChatStatus, ChatType
from maxo.fsm import State
from maxo.routing.interfaces import BaseRouter
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.routing.updates import ErrorEvent, MessageCallback, MessageCreated
from maxo.types import Message, MessageButton, Recipient, User


class ManagerImpl(DialogManager):
    def __init__(
        self,
        event: ChatEvent,
        message_manager: MessageManagerProtocol,
        media_id_storage: MediaIdStorageProtocol,
        registry: DialogRegistryProtocol,
        router: BaseRouter,
        ctx: Ctx,
        getter: DataGetter | None,
    ) -> None:
        self.disabled = False
        self.message_manager = message_manager
        self.media_id_storage = media_id_storage
        self._event = event
        self._ctx = ctx
        self._show_mode: ShowMode = ShowMode.AUTO
        self._registry = registry
        self._router = router
        self._getter = getter

    @property
    def show_mode(self) -> ShowMode:
        """Get current show mode, used for next show action."""
        return self._show_mode

    @show_mode.setter
    def show_mode(self, show_mode: ShowMode) -> None:
        """Set current show mode, used for next show action."""
        self._show_mode = show_mode

    @property
    def event(self) -> ChatEvent:
        return self._event

    @property
    def middleware_data(self) -> dict:
        """Middleware data."""
        return self._ctx

    @property
    def dialog_data(self) -> dict:
        """Dialog data for current context."""
        return self.current_context().dialog_data

    @property
    def start_data(self) -> Data:
        """Start data for current context."""
        return self.current_context().start_data

    def check_disabled(self) -> None:
        if self.disabled:
            raise IncorrectBackgroundError(
                "Detected background access to dialog manager. "
                "Please use background manager available via `manager.bg()` "
                "method to access methods from background tasks",
            )

    async def load_data(self) -> dict:
        context = self.current_context()
        if self._getter:
            data = await self._getter(**self.middleware_data)
        else:
            data = {}
        return {
            "dialog_data": context.dialog_data,
            "start_data": context.start_data,
            "middleware_data": self.middleware_data,
            "event": self.event,
            **data,
        }

    def is_preview(self) -> bool:
        return False

    def dialog(self) -> DialogProtocol:
        self.check_disabled()
        current = self.current_context()
        if not current:
            raise RuntimeError
        return self._registry.find_dialog(current.state)

    def current_context(self) -> Context:
        self.check_disabled()
        context = self._current_context_unsafe()
        if not context:
            loggers.dialogs.warning(
                "Trying to access current context, while no dialog is opened",
            )
            raise NoContextError
        return context

    def _current_context_unsafe(self) -> Context | None:
        return self._ctx.get(CONTEXT_KEY)

    def has_context(self) -> bool:
        self.check_disabled()
        return bool(self._current_context_unsafe())

    def current_stack(self) -> Stack:
        self.check_disabled()
        return self._ctx[STACK_KEY]

    def storage(self) -> StorageProxy:
        return self._ctx[STORAGE_KEY]

    async def _remove_kbd(self) -> None:
        if self.current_stack().last_message_id is None:
            return
        await self.message_manager.remove_kbd(
            bot=self._ctx["bot"],
            old_message=self._get_last_message(),
            show_mode=self._calc_show_mode(),
        )
        self.current_stack().last_message_id = None

    async def _process_last_dialog_result(
        self,
        start_data: Data,
        result: Any,
    ) -> None:
        """Process closing last dialog in stack."""
        await self._remove_kbd()

    async def done(
        self,
        result: Any = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        self.check_disabled()
        self.show_mode = show_mode or self.show_mode
        await self.dialog().process_close(result, self)
        old_context = self.current_context()
        await self.mark_closed()
        context = self._current_context_unsafe()
        if not context:
            await self._process_last_dialog_result(
                old_context.start_data,
                result,
            )
            return
        dialog = self.dialog()
        await dialog.process_result(old_context.start_data, result, self)
        new_context = self._current_context_unsafe()
        if new_context and context.id == new_context.id:
            await self.show(show_mode)

    async def answer_callback(self) -> None:
        if not isinstance(self.event, MessageCallback):
            return None
        if self.is_event_simulated():
            return None
        return await self.message_manager.answer_callback(
            bot=self._ctx["bot"],
            callback=self.event.callback,
        )

    async def mark_closed(self) -> None:
        self.check_disabled()
        storage = self.storage()
        stack = self.current_stack()
        await storage.remove_context(stack.pop())
        if stack.empty():
            self._ctx[CONTEXT_KEY] = None
        else:
            intent_id = stack.last_intent_id()
            self._ctx[CONTEXT_KEY] = await storage.load_context(intent_id)
        await storage.save_stack(stack)

    async def start(
        self,
        state: State,
        data: Data = None,
        mode: StartMode = StartMode.NORMAL,
        show_mode: ShowMode | None = None,
        access_settings: AccessSettings | None = None,
    ) -> None:
        self.check_disabled()
        self.show_mode = show_mode or self.show_mode
        if mode is StartMode.NORMAL:
            await self._start_normal(state, data, access_settings)
        elif mode is StartMode.RESET_STACK:
            await self.reset_stack(remove_keyboard=False)
            await self._start_normal(state, data, access_settings)
        elif mode is StartMode.NEW_STACK:
            await self._start_new_stack(state, data, access_settings)
        else:
            raise ValueError(f"Unknown start mode: {mode}")

    async def reset_stack(self, remove_keyboard: bool = True) -> None:
        self.check_disabled()
        storage = self.storage()
        stack = self.current_stack()
        while not stack.empty():
            await storage.remove_context(stack.pop())
        await storage.save_stack(stack)
        if remove_keyboard:
            await self._remove_kbd()
        self._ctx[CONTEXT_KEY] = None

    async def _start_new_stack(
        self,
        state: State,
        data: Data,
        access_settings: AccessSettings | None,
    ) -> None:
        stack = Stack()
        await self.bg(stack_id=stack.id).start(
            state,
            data,
            mode=StartMode.NORMAL,
            show_mode=self.show_mode,
            access_settings=access_settings,
        )

    async def _start_normal(
        self,
        state: State,
        data: Data,
        access_settings: AccessSettings | None,
    ) -> None:
        stack = self.current_stack()
        old_dialog: DialogProtocol | None = None
        if not stack.empty():
            old_dialog = self.dialog()
            if old_dialog.launch_mode is LaunchMode.EXCLUSIVE:
                raise ValueError(
                    "Cannot start dialog on top of one with launch_mode==SINGLE",
                )

        new_dialog = self._registry.find_dialog(state)
        await self._process_launch_mode(old_dialog, new_dialog)
        if self.has_context():
            await self.storage().save_context(self.current_context())
            if access_settings is None:
                access_settings = self.current_context().access_settings
        if access_settings is None:
            access_settings = stack.access_settings

        context = stack.push(state, data)
        context.access_settings = deepcopy(access_settings)
        self._ctx[CONTEXT_KEY] = context
        await self.dialog().process_start(self, data, state)
        new_context = self._current_context_unsafe()
        if new_context and context.id == new_context.id:
            await self.show()

    async def _process_launch_mode(
        self,
        old_dialog: DialogProtocol | None,
        new_dialog: DialogProtocol,
    ) -> None:
        if new_dialog.launch_mode in (LaunchMode.EXCLUSIVE, LaunchMode.ROOT):
            await self.reset_stack(remove_keyboard=False)
        if new_dialog.launch_mode is LaunchMode.SINGLE_TOP:  # noqa: SIM102
            if new_dialog is old_dialog:
                await self.storage().remove_context(self.current_stack().pop())
                self._ctx[CONTEXT_KEY] = None

    async def next(self, show_mode: ShowMode | None = None) -> None:
        context = self.current_context()
        states = self.dialog().states()
        current_index = states.index(context.state)
        if current_index + 1 >= len(states):
            raise ValueError(
                f"Cannot go to a non-existent state."
                f"The state of {current_index + 1} idx is requested, "
                f"but there are only {len(states)} states,"
                f"current state is {context.state}",
            )
        new_state = states[current_index + 1]
        await self.switch_to(new_state, show_mode)

    async def back(self, show_mode: ShowMode | None = None) -> None:
        context = self.current_context()
        states = self.dialog().states()
        current_index = states.index(context.state)
        if current_index - 1 < 0:
            raise ValueError(
                f"Cannot go to a non-existent state."
                f"The state of {current_index - 1} idx is requested, "
                f"but states idx should be positive"
                f"current state is {context.state}",
            )
        new_state = states[current_index - 1]
        await self.switch_to(new_state, show_mode)

    async def switch_to(
        self,
        state: State,
        show_mode: ShowMode | None = None,
    ) -> None:
        self.check_disabled()
        context = self.current_context()
        if context.state.group != state.group:
            raise ValueError(
                f"Cannot switch to another state group. "
                f"Current state: {context.state}, asked for {state}",
            )
        self.show_mode = show_mode or self.show_mode
        context.state = state

    def _ensure_stack_compatible(
        self,
        stack: Stack,
        new_message: NewMessage,
    ) -> None:
        if stack.id == DEFAULT_STACK_ID:
            return  # no limitations for default stack
        if any(
            isinstance(button, MessageButton)
            for button in itertools.chain(*(new_message.keyboard or []))
        ):
            raise InvalidKeyboardType(
                "Cannot use ReplyKeyboardMarkup in non default stack",
            )

    async def show(self, show_mode: ShowMode | None = None) -> None:
        try:
            stack = self.current_stack()
            bot = self._ctx["bot"]
            old_message = self._get_last_message()
            if self.show_mode is ShowMode.NO_UPDATE:
                loggers.dialogs.debug("ShowMode is NO_UPDATE, skip rendering")
                return

            new_message = await self.dialog().render(self)
            new_message.show_mode = show_mode or self.show_mode
            if new_message.show_mode is ShowMode.AUTO:
                new_message.show_mode = self._calc_show_mode()

            await self._load_cached_media(new_message)

            self._ensure_stack_compatible(stack, new_message)

            try:
                sent_message = await self.message_manager.show_message(
                    bot,
                    new_message,
                    old_message,
                )
            except MessageNotModified:
                # nothing changed so nothing to save
                # we do not have the actual version of message
                loggers.dialogs.debug("MessageNotModified, not storing ids")
            else:
                self._save_last_message(sent_message)

        except Exception as e:
            current_state = self.current_context().state
            e.add_note(f"maxo.dialogs state: {current_state}")
            raise

    async def _load_cached_media(self, new_message: NewMessage) -> None:
        for attachment in new_message.media:
            if attachment.media_id:
                continue
            attachment.media_id = await self.media_id_storage.get_media_id(
                path=attachment.path,
                url=attachment.url,
                type=attachment.type,
            )

    def is_event_simulated(self) -> bool:
        return bool(self.middleware_data.get(EVENT_SIMULATED))

    def _get_message_from_callback(
        self,
        event: MessageCallback,
    ) -> OldMessage | None:
        current_message = event.message
        stack = self.current_stack()
        if isinstance(current_message, Message):
            return OldMessage(
                text=current_message.body.text,
                recipient=current_message.recipient,
                message_id=current_message.body.mid,
                sequence_id=current_message.body.seq,
                attachments=current_message.body.attachments or [],
            )
        if not stack or not stack.last_message_id:
            return None
        return OldMessage(
            text=UnknownText.UNKNOWN,
            recipient=Recipient(
                user_id=event.callback.user.user_id,
                chat_id=None,
                chat_type=ChatType.CHAT,  # TODO: Узнать тип чата?
            ),
            message_id=stack.last_message_id,
            sequence_id=stack.last_sequence_id,
            attachments=stack.last_attachments,
        )

    def _get_last_message(self) -> OldMessage | None:
        if isinstance(self.event, ErrorEvent):
            event = self.event.update.update
        else:
            event = self.event
        if isinstance(event, MessageCallback):
            return self._get_message_from_callback(event)

        stack = self.current_stack()
        if not stack or not stack.last_message_id:
            return None
        event_context: EventContext = self.middleware_data[EVENT_CONTEXT_KEY]
        return OldMessage(
            text=UnknownText.UNKNOWN,
            recipient=Recipient(
                chat_id=event_context.chat_id,
                chat_type=event_context.chat_type,
                user_id=event_context.user_id,
            ),
            message_id=stack.last_message_id,
            sequence_id=stack.last_sequence_id,
            attachments=stack.last_attachments,
        )

    def _save_last_message(self, message: OldMessage) -> None:
        stack = self.current_stack()
        stack.last_message_id = message.message_id
        stack.last_sequence_id = message.sequence_id
        stack.last_attachments = message.attachments

    def _calc_show_mode(self) -> ShowMode:
        if self.show_mode is not ShowMode.AUTO:
            return self.show_mode
        if self.middleware_data[UPDATE_CONTEXT_KEY].chat_type != ChatType.DIALOG:
            return ShowMode.EDIT
        if self.current_stack().id != DEFAULT_STACK_ID:
            return ShowMode.EDIT
        if isinstance(self.event, MessageCreated):
            return ShowMode.SEND
        return ShowMode.EDIT

    async def update(
        self,
        data: dict | None = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        if data:
            self.current_context().dialog_data.update(data)
        await self.show(show_mode)

    def find(self, widget_id: str) -> Widget | None:
        widget = self.dialog().find(widget_id)
        if not widget:
            return None
        return widget.managed(self)

    def _get_fake_user(self, user_id: int | None = None) -> User:
        """Get User if we have info about him or FakeUser instead."""
        # TODO: Сделать нормально, это нейрослоп
        if isinstance(self.event, MessageCreated):
            current_user = self.event.message.unsafe_sender
        else:
            current_user = self.event.user
        ###

        if user_id is None or user_id == current_user.id:
            return current_user
        return FakeUser(
            user_id=user_id,
            is_bot=False,
            first_name="",
            last_activity_time=datetime.now(UTC),
        )

    def _get_fake_chat(self, chat_id: int | None = None) -> FakeChat:
        """Get Chat if we have info about him or FakeChat instead."""
        if update_context := self._ctx.get(UPDATE_CONTEXT_KEY):
            if chat_id is None or chat_id == update_context.chat_id:
                return FakeChat(
                    chat_id=update_context.chat_id,
                    type=update_context.chat_type,
                    is_public=False,
                    last_event_time=datetime.now(UTC),
                    participants_count=1,
                    status=ChatStatus.ACTIVE,
                )
        elif chat_id is None:
            raise ValueError(
                "Explicit `chat_id` is required for events without current chat",
            )
        return FakeChat(
            chat_id=chat_id,
            type="",
            is_public=False,
            last_event_time=datetime.now(UTC),
            participants_count=1,
            status=ChatStatus.ACTIVE,
        )

    def bg(
        self,
        user_id: int | None = None,
        chat_id: int | None = None,
        stack_id: str | None = None,
        load: bool = False,
    ) -> BaseDialogManager:
        user = self._get_fake_user(user_id)
        chat = self._get_fake_chat(chat_id)
        intent_id = None
        event_context = cast(
            "EventContext",
            self.middleware_data.get(EVENT_CONTEXT_KEY),
        )
        new_event_context = EventContext(
            bot=event_context.bot,
            user=user,
            user_id=user.id,
            chat=chat,
            chat_type=chat.type,
            chat_id=chat.id,
        )

        if stack_id is None:
            if event_context == new_event_context:
                stack_id = self.current_stack().id
                if self.has_context():
                    intent_id = self.current_context().id
            else:
                stack_id = DEFAULT_STACK_ID

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

    @asynccontextmanager
    async def fg(self) -> AsyncIterator[DialogManager]:
        yield self

    async def close_manager(self) -> None:
        self.check_disabled()
        self.disabled = True
        del self.media_id_storage
        del self.message_manager
        del self._event
        # del self._ctx
