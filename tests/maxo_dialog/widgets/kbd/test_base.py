from typing import Any

from magic_filter import F

from maxo.dialogs import DialogManager
from maxo.dialogs.api.internal import RawKeyboard
from maxo.dialogs.widgets.common import WhenCondition
from maxo.dialogs.widgets.kbd import Keyboard
from maxo.types import MessageButton


class Button(Keyboard):
    def __init__(self, id: str, when: WhenCondition = None) -> None:
        super().__init__(when=when, id=id)

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        assert self.widget_id is not None
        return [[MessageButton(text=self.widget_id)]]


async def test_or(mock_manager: DialogManager) -> None:
    text = Button("a") | Button("b")
    res = await text.render_keyboard({}, mock_manager)
    assert res == [[MessageButton(text="a")]]


async def test_or_condition(mock_manager: DialogManager) -> None:
    text = Button("A", when=F["a"]) | Button("B", when=F["b"]) | Button("C")
    res = await text.render_keyboard({"a": True}, mock_manager)
    assert res == [[MessageButton(text="A")]]
    res = await text.render_keyboard({"b": True}, mock_manager)
    assert res == [[MessageButton(text="B")]]
    res = await text.render_keyboard({}, mock_manager)
    assert res == [[MessageButton(text="C")]]
