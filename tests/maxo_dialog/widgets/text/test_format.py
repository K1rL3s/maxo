from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Format


async def test_render_format(mock_manager: DialogManager) -> None:
    format_widget = Format("Hello, {name}!")

    rendered_text = await format_widget.render_text(
        data={"name": "Tishka17"},
        manager=mock_manager,
    )

    assert rendered_text == "Hello, Tishka17!"
