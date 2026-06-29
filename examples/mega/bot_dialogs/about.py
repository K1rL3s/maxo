import importlib.metadata
from typing import Any

from maxo.dialogs.api.internal import TextWidget
from maxo.dialogs.dialog import Dialog
from maxo.dialogs.widgets.kbd import Cancel, Keyboard, Start
from maxo.dialogs.widgets.link_preview import LinkPreview
from maxo.dialogs.widgets.text import Const, Jinja
from maxo.dialogs.window import Window
from maxo.enums import TextFormat

from . import states


async def metadata_getter(**__: Any) -> dict[str, Any]:
    metadata = importlib.metadata.metadata("maxo")
    urls = [
        url.split(",", maxsplit=1)
        for url in (metadata.get_all("Project-Url") or ())
        if url
    ]
    return {
        "metadata": metadata,
        "urls": urls,
    }


about_dialog = Dialog(
    Window(
        Jinja(
            "<b><u>{{metadata.Name}}</u></b> by t.me/maxo_py\n"
            "\n"
            "{{metadata.Summary}}\n"
            "\n"
            "<b>Version:</b> {{metadata.Version}}\n"
            "<b>Author:</b> {{metadata['Author-email']}}\n"
            "\n"
            "{% for name, url in urls%}"
            '<b>{{name}}:</b> <a href="{{url}}">{{url}}</a>\n'
            "{% endfor %}"
            "",
        ),
        LinkPreview(is_disabled=True),
        Cancel(Const("Ok")),
        getter=metadata_getter,
        preview_data=metadata_getter,
        state=states.MaxoDialogStates.ABOUT,
        parse_mode=TextFormat.HTML,
    ),
)


DEFAULT_ABOUT_BTN_TEXT = Const("🗨️ About maxo.dialogs")


def about_maxo_dialogs_button(
    text: TextWidget = DEFAULT_ABOUT_BTN_TEXT,
) -> Keyboard:
    return Start(
        text=text,
        state=states.MaxoDialogStates.ABOUT,
        id="__aiogd_about__",
    )
