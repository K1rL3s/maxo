from collections.abc import MutableMapping, MutableSequence
from functools import partial
from typing import Any

from maxo.errors.routing import RouterAlreadyIncludedError
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces import BaseRouter, Observer
from maxo.routing.interfaces.router import RouterState
from maxo.routing.middlewares.state import (
    EmptyMiddlewareManagerState,
    StartedMiddlewareManagerState,
)
from maxo.routing.observers import SignalObserver, UpdateObserver
from maxo.routing.observers.state import EmptyObserverState, StartedObserverState
from maxo.routing.routers.state import EmptyRouterState, StartedRouterState
from maxo.routing.sentinels import UNHANDLED
from maxo.routing.signals.shutdown import AfterShutdown, BeforeShutdown
from maxo.routing.signals.startup import AfterStartup, BeforeStartup
from maxo.routing.utils.get_default_name import get_router_default_name
from maxo.types import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    ChatTitleChanged,
    CommentCreated,
    CommentEdited,
    CommentRemoved,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
    UserRemovedFromChat,
)
from maxo.types.error_event import ErrorEvent


class Router(BaseRouter):
    def __init__(self, name: str | None = None) -> None:
        self.bot_added_to_chat = UpdateObserver[BotAddedToChat]()
        self.bot_removed_from_chat = UpdateObserver[BotRemovedFromChat]()
        self.bot_started = UpdateObserver[BotStarted]()
        self.bot_stopped = UpdateObserver[BotStopped]()
        self.chat_title_changed = UpdateObserver[ChatTitleChanged]()
        self.comment_created = UpdateObserver[CommentCreated]()
        self.comment_edited = UpdateObserver[CommentEdited]()
        self.comment_removed = UpdateObserver[CommentRemoved]()
        self.dialog_cleared = UpdateObserver[DialogCleared]()
        self.dialog_muted = UpdateObserver[DialogMuted]()
        self.dialog_removed = UpdateObserver[DialogRemoved]()
        self.dialog_unmuted = UpdateObserver[DialogUnmuted]()
        self.message_callback = UpdateObserver[MessageCallback]()
        self.message_created = UpdateObserver[MessageCreated]()
        self.message_edited = UpdateObserver[MessageEdited]()
        self.message_removed = UpdateObserver[MessageRemoved]()
        self.user_added_to_chat = UpdateObserver[UserAddedToChat]()
        self.user_removed_from_chat = UpdateObserver[UserRemovedFromChat]()

        self.message = self.message_created  # Подражание aiogram
        self.callback_query = self.message_callback  # Подражание aiogram
        self.edited_message = self.message_edited  # Подражание aiogram

        self.exception = self.exceptions = self.error = self.errors = UpdateObserver[
            ErrorEvent[Any, Any]
        ]()

        self.before_startup = SignalObserver[BeforeStartup]()
        self.before_startup.handler(self._emit_before_startup_handler)

        self.after_startup = SignalObserver[AfterStartup]()

        self.before_shutdown = SignalObserver[BeforeShutdown]()
        self.before_shutdown.handler(self._emit_before_shutdown_handler)

        self.after_shutdown = SignalObserver[AfterShutdown]()

        self._observers: dict[Any, Observer[Any, Any, Any]] = {
            BotAddedToChat: self.bot_added_to_chat,
            BotRemovedFromChat: self.bot_removed_from_chat,
            BotStarted: self.bot_started,
            BotStopped: self.bot_stopped,
            ChatTitleChanged: self.chat_title_changed,
            CommentCreated: self.comment_created,
            CommentEdited: self.comment_edited,
            CommentRemoved: self.comment_removed,
            DialogCleared: self.dialog_cleared,
            DialogMuted: self.dialog_muted,
            DialogRemoved: self.dialog_removed,
            DialogUnmuted: self.dialog_unmuted,
            MessageCallback: self.message_callback,
            MessageCreated: self.message_created,
            MessageEdited: self.message_edited,
            MessageRemoved: self.message_removed,
            UserAddedToChat: self.user_added_to_chat,
            UserRemovedFromChat: self.user_removed_from_chat,
            ErrorEvent: self.exception,
            BeforeStartup: self.before_startup,
            AfterStartup: self.after_startup,
            BeforeShutdown: self.before_shutdown,
            AfterShutdown: self.after_shutdown,
        }

        if name is None:
            name = get_router_default_name()

        self._name = name
        self._children_routers: MutableSequence[BaseRouter] = []
        self._parent_router: BaseRouter | None = None
        self._state: RouterState = EmptyRouterState()

    def __repr__(self) -> str:
        return f"<Router {self._name!r}>"

    @property
    def state(self) -> RouterState:
        return self._state

    @state.setter
    def state(self, value: RouterState) -> None:
        self._state = value

    @property
    def name(self) -> str:
        return self._name

    @property
    def observers(self) -> MutableMapping[Any, Observer[Any, Any, Any]]:
        return self._observers

    @property
    def children_routers(self) -> MutableSequence[BaseRouter]:
        return self._children_routers

    def include(self, *routers: BaseRouter) -> None:
        self.state.ensure_include()
        for router in routers:
            if router.parent_router is not None:
                raise RouterAlreadyIncludedError(router, router.parent_router)
            router.parent_router = self
            self.children_routers.append(router)

    async def trigger_child(self, ctx: Ctx) -> Any:
        for child_router in self.children_routers:
            result = await child_router.trigger(ctx)
            if result is UNHANDLED:
                continue
            return result
        return UNHANDLED

    async def trigger(self, ctx: Ctx) -> Any:
        observer = self.observers.get(type(ctx["update"]))
        if observer is None:
            return await self.trigger_child(ctx)

        chain_middlewares = observer.middleware.outer.wrap_middlewares(
            partial(self._trigger, observer=observer),
        )
        return await chain_middlewares(ctx)

    async def _trigger(self, ctx: Ctx, *, observer: Observer[Any, Any, Any]) -> Any:
        if not await observer.execute_filter(ctx):
            return UNHANDLED

        result = await observer.handler_lookup(ctx)
        if result is UNHANDLED:
            return await self.trigger_child(ctx)
        return result

    async def _emit_before_startup_handler(
        self,
    ) -> None:
        self._state = StartedRouterState()

        for observer in self.observers.values():
            observer.state = StartedObserverState()

            observer.middleware.inner.state = StartedMiddlewareManagerState()
            observer.middleware.outer.state = StartedMiddlewareManagerState()

    async def _emit_before_shutdown_handler(self) -> None:
        self._state = EmptyRouterState()

        for observer in self.observers.values():
            observer.state = EmptyObserverState()

            observer.middleware.inner.state = EmptyMiddlewareManagerState()
            observer.middleware.outer.state = EmptyMiddlewareManagerState()

    @property
    def parent_router(self) -> BaseRouter | None:
        return self._parent_router

    @parent_router.setter
    def parent_router(self, value: BaseRouter | None) -> None:
        self._parent_router = value
