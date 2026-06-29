# ruff: noqa: SLF001 BLE001

import html
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import anyio
from jinja2 import Environment, PackageLoader, select_autoescape

from maxo import Bot, loggers
from maxo.dialogs.api.entities import (
    EVENT_CONTEXT_KEY,
    AccessSettings,
    ChatEvent,
    Context,
    Data,
    DialogAction,
    DialogUpdateEvent,
    EventContext,
    MediaAttachment,
    NewMessage,
    ShowMode,
    Stack,
    StartMode,
)
from maxo.dialogs.api.exceptions import NoContextError
from maxo.dialogs.api.protocols.dialog import DialogProtocol
from maxo.dialogs.api.protocols.manager import BaseDialogManager, DialogManager
from maxo.dialogs.manager.manager_middleware import MANAGER_KEY
from maxo.dialogs.setup import collect_dialogs
from maxo.dialogs.utils import split_reply_callback
from maxo.enums import AttachmentType
from maxo.enums.chat_type import ChatType
from maxo.fsm import State, StatesGroup
from maxo.routing.interfaces import BaseRouter
from maxo.routing.middlewares.update_context import (
    EVENT_FROM_USER_KEY,
    UPDATE_CONTEXT_KEY,
)
from maxo.routing.updates.message_callback import MessageCallback
from maxo.types import Callback, CallbackButton, UpdateContext, User
from maxo.types.message import Message
from maxo.types.message_body import MessageBody
from maxo.types.recipient import Recipient

if TYPE_CHECKING:
    from maxo.dialogs.api.internal.widgets import Widget
    from maxo.dialogs.dialog import Dialog


@dataclass
class RenderButton:
    state: str
    title: str


@dataclass
class RenderWindow:
    message: str
    state: str
    state_name: str
    keyboard: list[list[RenderButton]]
    reply_keyboard: list[list[RenderButton]]
    photo: str | None
    text_input: RenderButton | None
    attachment_input: RenderButton | None


@dataclass
class RenderDialog:
    state_group: str
    windows: list[RenderWindow]


class FakeManager(DialogManager):
    def __init__(self) -> None:
        self._event = DialogUpdateEvent(
            user=User(
                user_id=1,
                is_bot=False,
                first_name="Fake",
                last_activity_time=datetime(2024, 1, 1, tzinfo=UTC),
            ),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            bot=Bot("", warming_up=False),
            action=DialogAction.UPDATE,
            data={},
            intent_id=None,
            stack_id=None,
        )
        self._context: Context | None = None
        self._dialog: DialogProtocol | None = None
        self._data = {
            MANAGER_KEY: self,
            UPDATE_CONTEXT_KEY: UpdateContext(
                chat_id=self._event.recipient.chat_id,
                user_id=self._event.recipient.user_id,
                type=self._event.recipient.chat_type,
            ),
            EVENT_FROM_USER_KEY: self._event.user,
            EVENT_CONTEXT_KEY: EventContext(
                bot=self._event.bot,
                chat=None,
                chat_type=self._event.recipient.chat_type,
                chat_id=self._event.recipient.chat_id,
                user=self._event.user,
                user_id=self._event.user.user_id,
            ),
        }

    async def next(self, show_mode: ShowMode | None = None) -> None:
        states = self._dialog.states()
        current_index = states.index(self.current_context().state)
        if current_index + 1 >= len(states):
            raise ValueError(
                f"Cannot go to a non-existent state."
                f"The state of {current_index + 1} idx is requested, "
                f"but there are only {len(states)} states"
                f"current state is {self.current_context().state}",
            )
        new_state = states[current_index + 1]
        await self.switch_to(new_state, show_mode)

    async def back(self, show_mode: ShowMode | None = None) -> None:
        states = self._dialog.states()
        current_index = states.index(self.current_context().state)
        if current_index - 1 < 0:
            raise ValueError(
                f"Cannot go to a non-existent state."
                f"The state of {current_index - 1} idx is requested, "
                f"but states idx should be positive"
                f"current state is {self.current_context().state}",
            )
        new_state = states[current_index - 1]
        await self.switch_to(new_state, show_mode)

    @property
    def middleware_data(self) -> dict:
        return self._data

    @property
    def event(self) -> ChatEvent:
        return self._event

    async def load_data(self) -> dict:
        return {}

    async def close_manager(self) -> None:
        pass

    async def reset_stack(self, remove_keyboard: bool = True) -> None:
        self.reset_context()

    def set_dialog(self, dialog: "Dialog") -> None:
        self._dialog = dialog
        self.reset_context()

    def set_state(self, state: State) -> None:
        self.current_context().state = state

    def is_preview(self) -> bool:
        return True

    @property
    def dialog_data(self) -> dict:
        return self.current_context().dialog_data

    def reset_context(self) -> None:
        self._context = Context(
            _intent_id="0",
            _stack_id="0",
            start_data={},
            widget_data={},
            dialog_data={},
            state=State(),
        )

    async def switch_to(
        self,
        state: State,
        show_mode: ShowMode | None = None,
    ) -> None:
        self.set_state(state)

    async def start(
        self,
        state: State,
        data: Data = None,
        mode: StartMode = StartMode.NORMAL,
        show_mode: ShowMode = ShowMode.AUTO,
        access_settings: AccessSettings | None = None,
    ) -> None:
        self.set_state(state)

    async def done(
        self,
        result: Any = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        self.set_state(State("-"))

    def current_stack(self) -> Stack:
        return Stack()

    def current_context(self) -> Context:
        if not self._context:
            raise NoContextError
        return self._context

    def has_context(self) -> bool:
        return bool(self._context)

    async def show_raw(self) -> NewMessage:
        return await self._dialog.render(self)

    async def mark_closed(self) -> None:
        pass

    @property
    def start_data(self) -> Data:
        return {}

    @property
    def show_mode(self) -> ShowMode:
        return ShowMode.AUTO

    @show_mode.setter
    def show_mode(self, show_mode: ShowMode) -> None:
        return

    async def show(self, show_mode: ShowMode | None = None) -> None:
        pass

    def find(self, widget_id: str) -> Optional["Widget"]:
        widget = self._dialog.find(widget_id)
        if not widget:
            return None
        return widget.managed(self)

    async def update(
        self,
        data: dict | None = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        pass

    def bg(
        self,
        user_id: int | None = None,
        chat_id: int | None = None,
        stack_id: str | None = None,
        load: bool = False,
    ) -> BaseDialogManager:
        return self

    @asynccontextmanager
    async def fg(self) -> AsyncIterator[DialogManager]:
        yield self

    async def answer_callback(self) -> None:
        pass


def create_photo(media: MediaAttachment | None) -> str | None:
    if not media:
        return None
    if media.type != AttachmentType.IMAGE:
        return None
    if media.url:
        return media.url
    if media.path:
        return str(media.path)
    if media.media_id:
        return str(media.media_id)
    return None


async def create_button(
    title: str,
    callback: str,
    manager: FakeManager,
    state: State,
    dialog: "Dialog",
    simulate_events: bool,
) -> RenderButton:
    if not simulate_events:
        return RenderButton(title=title, state=state.state)
    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="",
        last_activity_time=datetime(2024, 1, 1, tzinfo=UTC),
    )
    message_callback = MessageCallback(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            payload=callback,
        ),
    )
    manager.set_state(state)
    try:
        await dialog._callback_handler(
            message_callback,
            ctx=manager.middleware_data,
            dialog_manager=manager,
        )
    except Exception:
        loggers.dialogs.debug("Click %s", callback)
    state = manager.current_context().state
    return RenderButton(title=title, state=state.state)


async def render_input(
    manager: FakeManager,
    state: State,
    dialog: "Dialog",
    content_type: str,
    simulate_events: bool,
) -> RenderButton | None:
    if not simulate_events:
        return None
    try:
        message = Message(
            timestamp=datetime.now(UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(),
        )
        manager.set_state(state)
        await dialog._message_handler(message, dialog_manager=manager)
    except Exception:
        loggers.dialogs.debug("Input %s", content_type)

    if state == manager.current_context().state:
        loggers.dialogs.debug("State not changed")
        return None
    loggers.dialogs.debug(
        "State changed %s >> %s",
        state,
        manager.current_context().state,
    )
    return RenderButton(
        title=content_type,
        state=manager.current_context().state.state,
    )


async def render_inline_keyboard(
    state: State,
    reply_markup: list[list[CallbackButton]],
    manager: FakeManager,
    dialog: "Dialog",
    simulate_events: bool,
) -> list[list[RenderButton]]:
    return [
        [
            await create_button(
                title=button.text,
                callback=button.payload,
                manager=manager,
                dialog=dialog,
                state=state,
                simulate_events=simulate_events,
            )
            for button in row
        ]
        for row in reply_markup
    ]


async def render_reply_keyboard(
    state: State,
    reply_markup: list[list[CallbackButton]],
    manager: FakeManager,
    dialog: "Dialog",
    simulate_events: bool,
) -> list[list[RenderButton]]:
    # TODO: Simulate events using keyboard
    keyboard = []
    for row in reply_markup:
        keyboard_row = []
        for button in row:
            text, data = split_reply_callback(button.text)
            keyboard_row.append(
                await create_button(
                    title=text,
                    callback=data,
                    manager=manager,
                    dialog=dialog,
                    state=state,
                    simulate_events=simulate_events,
                ),
            )
        keyboard.append(keyboard_row)
    return keyboard


async def create_window(
    state: State,
    message: NewMessage,
    manager: FakeManager,
    dialog: "Dialog",
    simulate_events: bool,
) -> RenderWindow:
    raw_text = message.text or ""
    text = html.escape(raw_text) if message.parse_mode is None else raw_text

    if message.keyboard is not None:
        keyboard = await render_inline_keyboard(
            state,
            message.keyboard,  # type: ignore[arg-type]
            manager,
            dialog,
            simulate_events,
        )
        reply_keyboard = []
    else:
        keyboard = []
        reply_keyboard = []

    return RenderWindow(
        message=text.replace("\n", "<br>"),
        state=state.state,
        state_name=state._state,
        photo=create_photo(media=message.media),
        keyboard=keyboard,
        reply_keyboard=reply_keyboard,
        text_input=await render_input(
            manager=manager,
            state=state,
            dialog=dialog,
            content_type=AttachmentType.TEXT,
            simulate_events=simulate_events,
        ),
        attachment_input=await render_input(
            manager=manager,
            state=state,
            dialog=dialog,
            content_type=AttachmentType.IMAGE,
            simulate_events=simulate_events,
        ),
    )


async def render_dialog(
    manager: FakeManager,
    group: type[StatesGroup],
    dialog: "Dialog",
    simulate_events: bool,
) -> RenderDialog:
    manager.set_dialog(dialog)
    windows = []
    for state in group.__states__:
        manager.set_state(state)
        new_message = await manager.show_raw()
        windows.append(
            await create_window(
                manager=manager,
                state=state,
                dialog=dialog,
                message=new_message,
                simulate_events=simulate_events,
            ),
        )

    return RenderDialog(state_group=str(group.__qualname__), windows=windows)


async def render_preview_content(
    router: BaseRouter,
    simulate_events: bool = False,
) -> str:
    fake_manager = FakeManager()
    dialogs = [
        await render_dialog(
            manager=fake_manager,
            group=dialog.states_group(),
            dialog=dialog,
            simulate_events=simulate_events,
        )
        for dialog in collect_dialogs(router)
    ]
    env = Environment(
        loader=PackageLoader("maxo.dialogs.tools"),
        autoescape=select_autoescape(),
    )
    template = env.get_template("message.html")
    return template.render(dialogs=dialogs)


async def render_preview(
    router: BaseRouter,
    file: str,
    simulate_events: bool = False,
) -> None:
    res = await render_preview_content(router, simulate_events)
    async with await anyio.open_file(Path(file), "w", encoding="utf-8") as f:
        await f.write(res)
