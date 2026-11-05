from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs import Window
from maxo.dialogs.api.entities import EVENT_CONTEXT_KEY, EventContext
from maxo.dialogs.widgets.input import MessageInput
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.link_preview import LinkPreview
from maxo.dialogs.widgets.media import StaticMedia
from maxo.dialogs.widgets.text import Const
from maxo.enums import ChatType
from maxo.fsm import State, StatesGroup


class SG(StatesGroup):
    first = State()


def make_dialog() -> MagicMock:
    return MagicMock(load_data=AsyncMock(return_value={}))


def make_manager() -> MagicMock:
    manager = MagicMock()
    manager.load_data = AsyncMock(return_value={})
    manager.is_preview = MagicMock(return_value=False)
    manager.current_context.return_value.id = "intent"
    manager.middleware_data = {
        "dialog_manager": manager,
        EVENT_CONTEXT_KEY: EventContext(
            bot=MagicMock(),
            chat=None,
            chat_id=10,
            chat_type=ChatType.DIALOG,
            user=MagicMock(),
            user_id=1,
        ),
    }
    return manager


class TestRender:
    async def test_render_media_without_media(self) -> None:
        window = Window(Const("t"), state=SG.first)

        assert await window.render_media({}, make_manager()) == []

    async def test_render_media_with_media(self) -> None:
        window = Window(
            Const("t"),
            StaticMedia(url="http://e.com/a.png"),
            state=SG.first,
        )

        media = await window.render_media({}, make_manager())

        assert len(media) == 1

    async def test_render_link_preview_without_widget(self) -> None:
        window = Window(Const("t"), state=SG.first)

        assert await window.render_link_preview({}, make_manager()) is None

    async def test_render_link_preview_with_widget(self) -> None:
        window = Window(
            Const("t"),
            LinkPreview(url=Const("http://e.com")),
            state=SG.first,
        )

        assert await window.render_link_preview({}, make_manager()) is not None

    async def test_render_builds_new_message(self) -> None:
        window = Window(
            Const("hello"),
            Button(Const("b"), id="btn"),
            state=SG.first,
        )

        message = await window.render(make_dialog(), make_manager())

        assert message.text == "hello"
        assert message.keyboard is not None

    async def test_render_reraises_getter_error(self) -> None:
        async def getter(**_kwargs: Any) -> dict[Any, Any]:
            raise RuntimeError("boom")

        window = Window(Const("t"), state=SG.first, getter=getter)

        with pytest.raises(RuntimeError, match="boom"):
            await window.render(make_dialog(), make_manager())


class TestCallbacks:
    async def test_process_callback_delegates_to_keyboard(self) -> None:
        window = Window(Const("t"), Button(Const("b"), id="btn"), state=SG.first)
        callback = MagicMock(payload="btn")

        result = await window.process_callback(callback, MagicMock(), make_manager())

        assert result is True

    async def test_process_result_without_handler(self) -> None:
        window = Window(Const("t"), state=SG.first)

        await window.process_result({}, None, make_manager())

    async def test_process_result_calls_handler(self) -> None:
        handler = AsyncMock()
        window = Window(Const("t"), state=SG.first, on_process_result=handler)

        await window.process_result({}, "res", make_manager())

        handler.assert_awaited_once()

    async def test_process_message_without_input(self) -> None:
        window = Window(Const("t"), state=SG.first)

        assert (
            await window.process_message(
                MagicMock(),
                MagicMock(),
                make_manager(),
            )
            is False
        )

    async def test_process_message_with_input(self) -> None:
        handler = AsyncMock(return_value=None)
        window = Window(Const("t"), MessageInput(handler), state=SG.first)

        await window.process_message(MagicMock(), MagicMock(), make_manager())

        handler.assert_awaited_once()


class TestFindAndRepr:
    def test_find_in_keyboard(self) -> None:
        button = Button(Const("b"), id="btn")
        window = Window(Const("t"), button, state=SG.first)

        assert window.find("btn") is button

    def test_find_missing(self) -> None:
        window = Window(Const("t"), state=SG.first)

        assert window.find("missing") is None

    def test_get_state(self) -> None:
        assert Window(Const("t"), state=SG.first).get_state() == SG.first

    def test_repr_contains_state(self) -> None:
        assert "SG:first" in repr(Window(Const("t"), state=SG.first))
