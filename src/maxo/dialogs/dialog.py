import contextlib
import dataclasses
from collections.abc import Awaitable, Callable
from typing import (
    Any,
    ParamSpec,
    TypeVar,
)

from maxo import Router, loggers
from maxo.dialogs.api.entities import Context, Data, LaunchMode, NewMessage
from maxo.dialogs.api.exceptions import UnregisteredWindowError
from maxo.dialogs.api.internal import Widget, WindowProtocol
from maxo.dialogs.api.protocols import (
    CancelEventProcessing,
    DialogManager,
    DialogProtocol,
)
from maxo.enums import ChatType
from maxo.errors import AttributeIsEmptyError
from maxo.fsm import State, StatesGroup
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces import BaseRouter
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.types.update_context import UpdateContext

from .context.intent_filter import IntentFilter
from .utils import remove_intent_id
from .widgets.data import PreviewAwareGetter
from .widgets.utils import GetterVariant, ensure_data_getter

OnDialogEvent = Callable[[Any, DialogManager], Awaitable]
OnResultEvent = Callable[[Data, Any, DialogManager], Awaitable]
_W = TypeVar("_W", bound=Widget)
_P = ParamSpec("_P")


class Dialog(Router, DialogProtocol):
    def __init__(
        self,
        *windows: WindowProtocol,
        on_start: OnDialogEvent | None = None,
        on_close: OnDialogEvent | None = None,
        on_process_result: OnResultEvent | None = None,
        launch_mode: LaunchMode = LaunchMode.STANDARD,
        getter: GetterVariant = None,
        preview_data: GetterVariant = None,
        name: str | None = None,
    ) -> None:
        if not windows:
            raise ValueError(
                "Dialog must have at least one window",
            )

        super().__init__(name=name or windows[0].get_state().group.__name__)
        self._states_group = windows[0].get_state().group
        self._states: list[State] = []
        for w in windows:
            if w.get_state().group != self._states_group:
                raise ValueError(
                    "All windows must be attached to same StatesGroup",
                )
            state = w.get_state()
            if state in self._states:
                raise ValueError(f"Multiple windows with state {state}")
            self._states.append(state)
        self.windows: dict[State, WindowProtocol] = dict(
            zip(self._states, windows, strict=False),
        )
        self.on_start = on_start
        self.on_close = on_close
        self.on_process_result = on_process_result
        self._launch_mode = launch_mode
        self.getter = PreviewAwareGetter(
            ensure_data_getter(getter),
            ensure_data_getter(preview_data),
        )
        self._setup_filter()
        self._register_handlers()

    @property
    def launch_mode(self) -> LaunchMode:
        return self._launch_mode

    def states(self) -> list[State]:
        return self._states

    async def process_start(
        self,
        manager: DialogManager,
        start_data: Data,
        state: State | None = None,
    ) -> None:
        if state is None:
            state = self._states[0]
        loggers.dialogs.debug("Dialog start: %s (%s)", state, self)
        await manager.switch_to(state)
        await self._process_callback(self.on_start, start_data, manager)

    async def _process_callback(
        self,
        callback: OnDialogEvent | None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None:
        if callback:
            await callback(*args, **kwargs)

    async def _current_window(
        self,
        manager: DialogManager,
    ) -> WindowProtocol:
        try:
            return self.windows[manager.current_context().state]
        except KeyError as e:
            raise UnregisteredWindowError(
                f"No window found for `{manager.current_context().state}` "
                f"Current state group is `{self.states_group_name()}`",
            ) from e

    async def load_data(
        self,
        manager: DialogManager,
    ) -> dict:
        data = await manager.load_data()
        data.update(await self.getter(**manager.middleware_data))
        return data

    async def render(self, manager: DialogManager) -> NewMessage:
        loggers.dialogs.debug("Dialog render (%s)", self)
        window = await self._current_window(manager)
        return await window.render(self, manager)

    async def _message_handler(
        self,
        message: MessageCreated,
        ctx: Ctx,
        dialog_manager: DialogManager,
    ) -> None:
        old_context = dialog_manager.current_context()
        window = await self._current_window(dialog_manager)
        try:
            processed = await window.process_message(
                message,
                self,
                dialog_manager,
            )
        except CancelEventProcessing:
            processed = False
        if self._need_refresh(processed, old_context, dialog_manager):
            await dialog_manager.show()

    async def _callback_handler(
        self,
        callback: MessageCallback,
        ctx: Ctx,
        dialog_manager: DialogManager,
    ) -> None:
        old_context = dialog_manager.current_context()
        _, payload = remove_intent_id(callback.callback.payload)

        cleaned_callback = dataclasses.replace(callback.callback, payload=payload)
        cleaned_event = dataclasses.replace(callback, callback=cleaned_callback)

        with contextlib.suppress(AttributeIsEmptyError):
            bot = callback.bot
            cleaned_callback.as_(bot)
            cleaned_event.as_(bot)
            if cleaned_event.message:
                cleaned_event.message.as_(bot)

        window = await self._current_window(dialog_manager)
        try:
            processed = await window.process_callback(
                cleaned_event,
                self,
                dialog_manager,
            )
        except CancelEventProcessing:
            processed = False
        if self._need_refresh(processed, old_context, dialog_manager):
            await dialog_manager.show()
        await dialog_manager.answer_callback()

    def _need_refresh(
        self,
        processed: bool,
        old_context: Context,
        dialog_manager: DialogManager,
    ) -> bool:
        if not dialog_manager.has_context():
            # nothing to show
            return False
        if dialog_manager.current_context() != old_context:
            # dialog switched, so it is already refreshed
            return False
        if processed:
            # something happened
            return True
        update_context: UpdateContext = dialog_manager.middleware_data[
            UPDATE_CONTEXT_KEY
        ]
        if update_context.chat_type == ChatType.DIALOG:  # noqa: SIM103
            # for private chats we can ensure dialog is visible
            return True
        return False

    def _setup_filter(self) -> None:
        intent_filter = IntentFilter(
            aiogd_intent_state_group=self.states_group(),
        )
        for observer in self.observers.values():
            observer.filter(intent_filter)

    def _register_handlers(self) -> None:
        self.message_callback.handler(self._callback_handler)
        self.message_created.handler(self._message_handler)

    def states_group(self) -> type[StatesGroup]:
        return self._states_group

    def states_group_name(self) -> str:
        return self._states_group.__full_group_name__

    async def process_result(
        self,
        start_data: Data,
        result: Any,
        manager: DialogManager,
    ) -> None:
        context = manager.current_context()
        await self._process_callback(
            self.on_process_result,
            start_data,
            result,
            manager,
        )
        if context.id == manager.current_context().id:
            await self.windows[context.state].process_result(
                start_data,
                result,
                manager,
            )

    def include(self, *routers: BaseRouter) -> None:
        raise TypeError("Dialog cannot include routers")

    async def process_close(
        self,
        result: Any,
        manager: DialogManager,
    ) -> None:
        await self._process_callback(self.on_close, result, manager)

    def find(self, widget_id: str) -> _W | None:
        for w in self.windows.values():
            widget = w.find(widget_id)
            if widget:
                return widget
        return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}({self.states_group()})>"
