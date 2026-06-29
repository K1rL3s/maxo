from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Clipboard
from maxo.dialogs.widgets.text import Const
from maxo.types import ClipboardButton


async def test_render_clipboard(mock_manager: DialogManager) -> None:
    clipboard_widget = Clipboard(
        Const("Copy this text"),
        Const("Text to be copied to clipboard"),
    )

    keyboard = await clipboard_widget.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, ClipboardButton)
    assert button.text == "Copy this text"
    assert button.payload == "Text to be copied to clipboard"
