from maxo.dialogs import Dialog, LaunchMode, Window
from maxo.dialogs.widgets.kbd import Start
from maxo.dialogs.widgets.text import Const

from . import states
from .about import about_maxo_dialogs_button

main_dialog = Dialog(
    Window(
        Const("This is maxo.dialogs demo application"),
        Const("Use buttons below to see some options."),
        Start(
            text=Const("📐 Layout widgets"),
            id="layout",
            state=states.Layouts.MAIN,
        ),
        Start(
            text=Const("📜 Scrolling widgets"),
            id="scrolls",
            state=states.Scrolls.MAIN,
        ),
        Start(
            text=Const("☑️ Selection widgets"),
            id="selects",
            state=states.Selects.MAIN,
        ),
        Start(
            text=Const("📅 Date and time"),
            id="cal",
            state=states.Calendar.MAIN,
        ),
        Start(
            text=Const("💯 Counter and Progress"),
            id="counter",
            state=states.Counter.MAIN,
        ),
        Start(
            text=Const("🎛 Combining widgets"),
            id="multiwidget",
            state=states.Multiwidget.MAIN,
        ),
        Start(
            text=Const("🔢 Multiple steps"),
            id="switch",
            state=states.Switch.MAIN,
        ),
        Start(
            text=Const("🔗 Link Preview"),
            id="linkpreview",
            state=states.LinkPreview.MAIN,
        ),
        about_maxo_dialogs_button(),
        state=states.Main.MAIN,
    ),
    launch_mode=LaunchMode.ROOT,
)
