from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Const, Multi


async def test_render_multi(mock_manager: DialogManager) -> None:
    multi = Multi(
        Const("Hello!"),
        Const("And goodbye!"),
        sep=" ",
    )

    rendered_text = await multi.render_text(
        data={},
        manager=mock_manager,
    )

    assert rendered_text == "Hello! And goodbye!"
