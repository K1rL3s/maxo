from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Url
from maxo.dialogs.widgets.text import Const
from maxo.types import LinkButton


async def test_render_url(mock_manager: DialogManager) -> None:
    url = Url(
        Const("Github"),
        Const("https://github.com/Tishka17/aiogram_dialog/"),
    )

    keyboard = await url.render_keyboard(data={}, manager=mock_manager)

    button = keyboard[0][0]
    assert isinstance(button, LinkButton)
    assert button.text == "Github"
    assert button.url == "https://github.com/Tishka17/aiogram_dialog/"
