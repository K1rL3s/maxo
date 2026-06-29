from typing import Any

from maxo.dialogs import Dialog, Window
from maxo.dialogs.widgets.kbd import SwitchTo
from maxo.dialogs.widgets.link_preview import LinkPreview
from maxo.dialogs.widgets.text import Const, Format

from . import states
from .common import MAIN_MENU_BUTTON


async def links_getter(**__: Any) -> dict[str, Any]:
    return {
        "main": "https://github.com/K1rL3s",
        "photo": "https://github.com/K1rL3s/maxo",
    }


LinkPreview_MAIN_MENU_BUTTON = SwitchTo(
    text=Const("Back"),
    id="back",
    state=states.LinkPreview.MAIN,
)
COMMON_TEXT = Format(
    "This is demo of different link preview options.\n"
    "Link in text: {main}\n"
    "Link in preview can be different\n\n"
    "Current mode is:",
)

link_preview_dialog = Dialog(
    Window(
        COMMON_TEXT,
        Format("Default"),
        SwitchTo(
            Const("disable"),
            "_disable",
            states.LinkPreview.IS_DISABLED,
        ),
        SwitchTo(
            Const("enable"),
            "_enable",
            states.LinkPreview.IS_ENABLED,
        ),
        MAIN_MENU_BUTTON,
        state=states.LinkPreview.MAIN,
    ),
    Window(
        COMMON_TEXT,
        Const("is_disabled=True"),
        LinkPreview(is_disabled=True),
        LinkPreview_MAIN_MENU_BUTTON,
        state=states.LinkPreview.IS_DISABLED,
    ),
    Window(
        COMMON_TEXT,
        Const("is_disabled=False"),
        LinkPreview(is_disabled=False),
        LinkPreview_MAIN_MENU_BUTTON,
        state=states.LinkPreview.IS_ENABLED,
    ),
    getter=links_getter,
)
