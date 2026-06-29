from typing import Any, cast

from maxo.dialogs import Dialog, DialogManager, Window
from maxo.dialogs.widgets.kbd import (
    Back,
    Checkbox,
    ManagedCheckbox,
    ManagedRadio,
    Next,
    Radio,
    Row,
)
from maxo.dialogs.widgets.text import Case, Const, Format

from . import states
from .common import MAIN_MENU_BUTTON

HEADER = Const(
    "Multiple windows in the same dialog can be used "
    "to provide step by step user data input.\n",
)
CHECKBOX_ID = "chk"
EMOJI_ID = "emoji"


async def data_getter(
    dialog_manager: DialogManager,
    **__: Any,
) -> dict[str, Any]:
    checkbox = cast(ManagedCheckbox, dialog_manager.find(CHECKBOX_ID))
    radio = cast(ManagedRadio, dialog_manager.find(EMOJI_ID))
    return {
        "option": checkbox.is_checked(),
        "emoji": radio.get_checked() or "-",
    }


main_window = Window(
    HEADER,
    Const("Step 1. Press Next"),
    Next(),
    MAIN_MENU_BUTTON,
    state=states.Switch.MAIN,
)

input_window = Window(
    HEADER,
    Const("Step 2. Select options"),
    Checkbox(
        Const("✓ Option is enabled"),
        Const("Click to enable the option"),
        id=CHECKBOX_ID,
    ),
    Radio(
        checked_text=Format("🔘 {item}"),
        unchecked_text=Format("⚪️ {item}"),
        items=["😆", "😱", "😈", "🤖", "🤡"],
        item_id_getter=lambda x: x,
        id=EMOJI_ID,
    ),
    Row(Back(), Next()),
    MAIN_MENU_BUTTON,
    state=states.Switch.INPUT,
)

last_window = Window(
    HEADER,
    Const("Step 3. Your data:"),
    Case(
        {
            True: Const("Option: enabled"),
            False: Const("Option: disabled"),
        },
        selector="option",
    ),
    Format("Selected emoji: {emoji}"),
    Back(),
    MAIN_MENU_BUTTON,
    state=states.Switch.LAST,
    getter=data_getter,
)

switch_dialog = Dialog(
    main_window,
    input_window,
    last_window,
)
