from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Case, Const, Format


async def test_render_case(mock_manager: DialogManager) -> None:
    case = Case(
        {
            0: Format("{number} is even!"),
            1: Const("It is Odd"),
        },
        selector=F["number"] % 2,
    )

    rendered_text = await case.render_text(
        data={"number": 10},
        manager=mock_manager,
    )

    assert rendered_text == "10 is even!"
