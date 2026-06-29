from maxo.dialogs.widgets.kbd import Start
from maxo.dialogs.widgets.text import Const

from . import states

MAIN_MENU_BUTTON = Start(
    text=Const("☰ Main menu"),
    id="__main__",
    state=states.Main.MAIN,
)
