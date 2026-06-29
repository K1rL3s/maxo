from maxo.dialogs import Dialog, Window
from maxo.dialogs.widgets.kbd import Checkbox, Counter, Multiselect, Radio
from maxo.dialogs.widgets.text import Const, Format

from . import states
from .common import MAIN_MENU_BUTTON

multiwidget_dialog = Dialog(
    Window(
        Const("Multiple widgets in one window.\n"),
        Format("Your name: {event.callback.user.first_name}"),
        Checkbox(
            checked_text=Const("✓ Checkbox"),
            unchecked_text=Const(" Checkbox"),
            id="chk",
        ),
        Radio(
            checked_text=Format("🔘 {item}"),
            unchecked_text=Format("⚪️ {item}"),
            items=["A", "B", "C", "D"],
            item_id_getter=lambda x: x,
            id="radio1",
        ),
        Multiselect(
            checked_text=Format("✓ {item}"),
            unchecked_text=Format("{item}"),
            items=["😆", "😱", "🤯", "😈", "🤖", "👻", "🤡"],
            item_id_getter=lambda x: x,
            id="radio2",
        ),
        Counter(
            id="counter",
            default=0,
            max_value=10,
        ),
        MAIN_MENU_BUTTON,
        state=states.Multiwidget.MAIN,
    ),
)
