from collections.abc import Callable, Iterable
from typing import Any

from maxo import Ctx, Dispatcher, Router
from maxo.dialogs.api.entities import (
    DialogStartEvent,
    DialogSwitchEvent,
    DialogUpdateEvent,
)
from maxo.dialogs.api.entities.update_event import DialogFgEvent
from maxo.dialogs.api.exceptions import UnregisteredDialogError
from maxo.dialogs.api.internal import DataGetter, DialogManagerFactory
from maxo.dialogs.api.protocols import (
    BgManagerFactory,
    DialogProtocol,
    DialogRegistryProtocol,
    MediaIdStorageProtocol,
    MessageManagerProtocol,
    StackAccessValidator,
)
from maxo.dialogs.context.access_validator import DefaultAccessValidator
from maxo.dialogs.context.intent_middleware import (
    IntentErrorMiddleware,
    IntentMiddlewareFactory,
    context_saver_middleware,
    context_unlocker_middleware,
)
from maxo.dialogs.context.media_storage import MediaIdStorage
from maxo.dialogs.manager.bg_manager import BgManagerFactoryImpl
from maxo.dialogs.manager.manager_factory import DefaultManagerFactory
from maxo.dialogs.manager.manager_middleware import (
    BgFactoryMiddleware,
    ManagerMiddleware,
)
from maxo.dialogs.manager.message_manager import MessageManager
from maxo.dialogs.manager.update_handler import handle_aiogd_update
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.base import BaseEventIsolation
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.interfaces import BaseRouter
from maxo.routing.observers import UpdateObserver


def _setup_event_observer(router: Router) -> None:
    dialog_events_observer: UpdateObserver[DialogUpdateEvent] = UpdateObserver()
    router.observers[DialogUpdateEvent] = dialog_events_observer
    router.observers[DialogStartEvent] = dialog_events_observer
    router.observers[DialogSwitchEvent] = dialog_events_observer
    router.observers[DialogFgEvent] = dialog_events_observer


def _register_event_handler(
    router: Router,
    callback: Callable[..., Any],
) -> None:
    router.observers[DialogUpdateEvent].handler(callback)


class DialogRegistry(DialogRegistryProtocol):
    def __init__(self, router: Router) -> None:
        self.router = router
        self._loaded = False
        self._dialogs: dict[type[StatesGroup], DialogProtocol] = {}
        self._states_groups: dict[str, type[StatesGroup]] = {}

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.refresh()

    def find_dialog(self, state: State | str) -> DialogProtocol:
        self._ensure_loaded()
        group = (
            self._states_groups.get(state) if isinstance(state, str) else state.group
        )
        dialog = self._dialogs.get(group) if group is not None else None
        if dialog is None:
            raise UnregisteredDialogError(
                f"No dialog found for `{group if group is not None else state}` "
                f"(looking by state `{state}`)",
            )
        return dialog

    def states_groups(self) -> dict[str, type[StatesGroup]]:
        self._ensure_loaded()
        return self._states_groups

    def refresh(self) -> None:
        for dialog in collect_dialogs(self.router):
            states_group = dialog.states_group()
            if states_group in self._dialogs:
                existing_dialog = self._dialogs[states_group]
                raise ValueError(
                    f"StatesGroup '{states_group.__name__}' "
                    f"is used in multiple dialogs: "
                    f"'{existing_dialog}' and '{dialog}'",
                )
            self._dialogs[states_group] = dialog

        self._states_groups = {
            d.states_group_name(): d.states_group() for d in self._dialogs.values()
        }
        self._loaded = True


def _startup_callback(
    registry: DialogRegistry,
) -> Callable[..., Any]:
    async def _setup_dialogs(ctx: Ctx) -> None:
        registry.refresh()

    return _setup_dialogs


def _register_middleware(
    router: Router,
    dialog_manager_factory: DialogManagerFactory,
    bg_manager_factory: BgManagerFactory,
    stack_access_validator: StackAccessValidator,
    events_isolation: BaseEventIsolation,
) -> None:
    registry = DialogRegistry(router)
    manager_middleware = ManagerMiddleware(
        dialog_manager_factory=dialog_manager_factory,
        router=router,
        registry=registry,
    )
    intent_middleware = IntentMiddlewareFactory(
        registry=registry,
        access_validator=stack_access_validator,
        events_isolation=events_isolation,
    )
    # delayed configuration of middlewares
    router.after_startup.handler(_startup_callback(registry))

    dialog_updates_handler = router.observers[DialogUpdateEvent]

    router.exception.middleware.inner(
        IntentErrorMiddleware(
            registry=registry,
            events_isolation=events_isolation,
            access_validator=stack_access_validator,
        ),
    )
    router.message_created.middleware.outer(intent_middleware.process_message)
    router.message_callback.middleware.outer(intent_middleware.process_callback)
    router.bot_started.middleware.outer(intent_middleware.process_bot_started)
    router.bot_stopped.middleware.outer(intent_middleware.process_bot_stopped)
    router.user_added_to_chat.middleware.outer(
        intent_middleware.process_user_added_to_chat,
    )
    router.user_removed_from_chat.middleware.outer(
        intent_middleware.process_user_removed_from_chat,
    )
    router.bot_added_to_chat.middleware.outer(
        intent_middleware.process_bot_added_to_chat,
    )
    router.bot_removed_from_chat.middleware.outer(
        intent_middleware.process_bot_removed_from_chat,
    )
    router.bot_admin_permissions_changed.middleware.outer(
        intent_middleware.process_bot_admin_permissions_changed,
    )
    dialog_updates_handler.middleware.outer(intent_middleware.process_aiogd_update)

    router.message_created.middleware.outer(context_unlocker_middleware)
    router.message_callback.middleware.outer(context_unlocker_middleware)
    router.bot_started.middleware.outer(context_unlocker_middleware)
    router.bot_stopped.middleware.outer(context_unlocker_middleware)
    router.user_added_to_chat.middleware.outer(context_unlocker_middleware)
    router.user_removed_from_chat.middleware.outer(context_unlocker_middleware)
    router.bot_added_to_chat.middleware.outer(context_unlocker_middleware)
    router.bot_removed_from_chat.middleware.outer(context_unlocker_middleware)
    router.bot_admin_permissions_changed.middleware.outer(context_unlocker_middleware)
    dialog_updates_handler.middleware.outer(context_unlocker_middleware)

    router.message_created.middleware.inner(manager_middleware)
    router.message_callback.middleware.inner(manager_middleware)
    router.bot_started.middleware.inner(manager_middleware)
    router.bot_stopped.middleware.inner(manager_middleware)
    router.user_added_to_chat.middleware.inner(manager_middleware)
    router.user_removed_from_chat.middleware.inner(manager_middleware)
    router.bot_added_to_chat.middleware.inner(manager_middleware)
    router.bot_removed_from_chat.middleware.inner(manager_middleware)
    router.bot_admin_permissions_changed.middleware.inner(manager_middleware)
    router.exception.middleware.inner(manager_middleware)  # type: ignore[arg-type]
    dialog_updates_handler.middleware.inner(manager_middleware)

    router.message_created.middleware.inner(context_saver_middleware)
    router.message_callback.middleware.inner(context_saver_middleware)
    router.bot_started.middleware.inner(context_saver_middleware)
    router.bot_stopped.middleware.inner(context_saver_middleware)
    router.user_added_to_chat.middleware.inner(context_saver_middleware)
    router.user_removed_from_chat.middleware.inner(context_saver_middleware)
    router.bot_added_to_chat.middleware.inner(context_saver_middleware)
    router.bot_removed_from_chat.middleware.inner(context_saver_middleware)
    router.bot_admin_permissions_changed.middleware.inner(context_saver_middleware)
    dialog_updates_handler.middleware.inner(context_saver_middleware)

    bg_factory_middleware = BgFactoryMiddleware(bg_manager_factory)
    for observer in dict.fromkeys(router.observers.values()):
        observer.middleware.outer(bg_factory_middleware)


def _prepare_dialog_manager_factory(
    dialog_manager_factory: DialogManagerFactory | None,
    message_manager: MessageManagerProtocol | None,
    media_id_storage: MediaIdStorageProtocol | None,
    getter: DataGetter | None,
) -> DialogManagerFactory:
    if dialog_manager_factory is not None:
        return dialog_manager_factory
    if media_id_storage is None:
        media_id_storage = MediaIdStorage()
    if message_manager is None:
        message_manager = MessageManager(media_id_storage=media_id_storage)
    return DefaultManagerFactory(
        message_manager=message_manager,
        media_id_storage=media_id_storage,
        getter=getter,
    )


def _prepare_stack_access_validator(
    stack_access_validator: StackAccessValidator | None,
) -> StackAccessValidator:
    if stack_access_validator:
        return stack_access_validator
    return DefaultAccessValidator()


def _prepare_events_isolation(
    events_isolation: BaseEventIsolation | None,
) -> BaseEventIsolation:
    if events_isolation:
        return events_isolation
    return SimpleEventIsolation(DefaultKeyBuilder(with_destiny=True))


def collect_dialogs(router: BaseRouter) -> Iterable[DialogProtocol]:
    if isinstance(router, DialogProtocol):
        yield router
    for sub_router in router.children_routers:
        yield from collect_dialogs(sub_router)


def setup_dialogs(
    router: Dispatcher,
    *,
    dialog_manager_factory: DialogManagerFactory | None = None,
    message_manager: MessageManagerProtocol | None = None,
    media_id_storage: MediaIdStorageProtocol | None = None,
    stack_access_validator: StackAccessValidator | None = None,
    events_isolation: BaseEventIsolation | None = None,
    getter: DataGetter | None = None,
) -> BgManagerFactory:
    _setup_event_observer(router)
    _register_event_handler(router, handle_aiogd_update)

    dialog_manager_factory = _prepare_dialog_manager_factory(
        dialog_manager_factory=dialog_manager_factory,
        message_manager=message_manager,
        media_id_storage=media_id_storage,
        getter=getter,
    )
    stack_access_validator = _prepare_stack_access_validator(
        stack_access_validator,
    )
    events_isolation = _prepare_events_isolation(events_isolation)
    bg_manager_factory = BgManagerFactoryImpl(router)
    _register_middleware(
        router=router,
        dialog_manager_factory=dialog_manager_factory,
        bg_manager_factory=bg_manager_factory,
        stack_access_validator=stack_access_validator,
        events_isolation=events_isolation,
    )
    return bg_manager_factory
