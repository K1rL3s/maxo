from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import ListGroup
from maxo.dialogs.widgets.kbd.button import Button, Url
from maxo.dialogs.widgets.text import Const, Format
from maxo.types import CallbackButton, LinkButton


async def test_render_list_group_with_url_button(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Url(Const("Url"), url=Const("https://test.com")),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    keyboard = await list_group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 3
    assert len(keyboard[0]) == 1
    button = keyboard[0][0]
    assert isinstance(button, LinkButton)
    assert button.text == "Url"
    assert button.url == "https://test.com"


async def test_render_list_group_with_callback_button(
    mock_manager: DialogManager,
) -> None:
    list_group = ListGroup(
        Button(Format("Callback {item}"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    keyboard = await list_group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 3

    assert len(keyboard[0]) == 1
    button = keyboard[0][0]
    assert isinstance(button, CallbackButton)
    assert button.text == "Callback a"
    assert button.payload == "list:a:button"

    assert len(keyboard[2]) == 1
    button = keyboard[1][0]
    assert isinstance(button, CallbackButton)
    assert button.text == "Callback b"
    assert button.payload == "list:b:button"

    assert len(keyboard[2]) == 1
    button = keyboard[2][0]
    assert isinstance(button, CallbackButton)
    assert button.text == "Callback c"
    assert button.payload == "list:c:button"
