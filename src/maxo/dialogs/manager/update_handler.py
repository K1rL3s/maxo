from maxo import loggers
from maxo.dialogs.api.entities import (
    DialogAction,
    DialogStartEvent,
    DialogSwitchEvent,
    DialogUpdateEvent,
    ShowMode,
)
from maxo.dialogs.api.entities.update_event import DialogFgEvent
from maxo.dialogs.api.protocols import DialogManager


async def handle_aiogd_update(
    event: DialogUpdateEvent,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.show_mode = event.show_mode or ShowMode.AUTO
    if isinstance(event, DialogStartEvent):
        await dialog_manager.start(
            state=event.new_state,
            data=event.data,
            mode=event.mode,
            show_mode=event.show_mode,
            access_settings=event.access_settings,
        )
    elif isinstance(event, DialogSwitchEvent):
        await dialog_manager.switch_to(state=event.new_state)
        await dialog_manager.show()
    elif isinstance(event, DialogFgEvent):
        event.entered.set_result(dialog_manager)
        await event.exited
    elif event.action is DialogAction.UPDATE:
        if not dialog_manager.has_context():
            loggers.dialogs.warning("No context found")
            return
        if event.data:
            for k, v in event.data.items():
                dialog_manager.current_context().dialog_data[k] = v
        await dialog_manager.show()
    elif event.action is DialogAction.DONE:
        await dialog_manager.done(result=event.data)
