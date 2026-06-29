from typing import Any, cast

from maxo.dialogs import Dialog, DialogManager, Window
from maxo.dialogs.widgets.kbd import Counter, ManagedCounter
from maxo.dialogs.widgets.text import Const, Progress
from maxo.routing.updates import MessageCallback

from . import states
from .common import MAIN_MENU_BUTTON

ID_COUNTER = "counter"
MAX_VALUE = 10
FIELD_PROGRESS = "progress"


async def getter(dialog_manager: DialogManager, **__: Any) -> dict[str, Any]:
    counter = cast(ManagedCounter, dialog_manager.find(ID_COUNTER))
    return {
        FIELD_PROGRESS: counter.get_value() / MAX_VALUE * 100,
    }


async def on_text_click(
    callback: MessageCallback,
    widget: ManagedCounter,
    dialog_manager: DialogManager,
) -> None:
    await callback.callback_answer(f"Value: {widget.get_value()}")


counter_dialog = Dialog(
    Window(
        Const("`Counter` widget is used to create +/- buttons."),
        Const("`Progress` widget shows percentage\n"),
        Progress(field=FIELD_PROGRESS),
        Counter(
            id=ID_COUNTER,
            default=0,
            max_value=MAX_VALUE,
            on_text_click=on_text_click,
        ),
        MAIN_MENU_BUTTON,
        state=states.Counter.MAIN,
        getter=getter,
    ),
)
