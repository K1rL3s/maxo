from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo import Dispatcher
from maxo.dialogs import Dialog, DialogManager, DialogProtocol, Window
from maxo.dialogs.api.entities import MediaAttachment, MediaId, ShowMode
from maxo.dialogs.api.exceptions import NoContextError
from maxo.dialogs.manager.sub_manager import SubManager
from maxo.dialogs.tools.preview import (
    FakeManager,
    RenderButton,
    create_button,
    create_photo,
    render_dialog,
    render_input,
    render_preview,
    render_preview_content,
    render_reply_keyboard,
)
from maxo.dialogs.utils import join_reply_callback
from maxo.dialogs.widgets.input import TextInput
from maxo.dialogs.widgets.kbd import Back, Button, Cancel, ListGroup, Next, Row
from maxo.dialogs.widgets.media import StaticMedia
from maxo.dialogs.widgets.text import Const
from maxo.enums import AttachmentType
from maxo.fsm import State, StatesGroup
from maxo.types import CallbackButton


class SG(StatesGroup):
    first = State()
    second = State()


def make_dialog() -> Dialog:
    return Dialog(
        Window(
            Const("Первое окно"),
            StaticMedia(url="https://example.com/pic.png"),
            Row(
                Button(Const("Кнопка"), id="btn"),
                Next(),
            ),
            TextInput(id="inp"),
            state=SG.first,
        ),
        Window(
            Const("Второе окно\nс переносом"),
            Row(Back(), Cancel()),
            state=SG.second,
        ),
    )


def make_router() -> Dispatcher:
    dp = Dispatcher()
    dp.include(make_dialog())
    return dp


def test_create_photo_url() -> None:
    media = MediaAttachment(type=AttachmentType.IMAGE, url="https://e.com/a.png")

    assert create_photo(media) == "https://e.com/a.png"


def test_create_photo_path(tmp_path: Path) -> None:
    path = tmp_path / "a.png"
    media = MediaAttachment(type=AttachmentType.IMAGE, path=path)

    assert create_photo(media) == str(path)


def test_create_photo_none_and_non_image() -> None:
    assert create_photo(None) is None

    video = MediaAttachment(type=AttachmentType.VIDEO, url="https://e.com/a.mp4")
    assert create_photo(video) is None


async def test_render_preview_content_without_simulation() -> None:
    html = await render_preview_content(make_router(), simulate_events=False)

    assert "Первое окно" in html
    assert "Второе окно" in html
    assert "https://example.com/pic.png" in html


async def test_render_preview_content_with_simulation() -> None:
    html = await render_preview_content(make_router(), simulate_events=True)

    assert "Первое окно" in html
    assert "Второе окно" in html


async def test_render_preview_escapes_text_without_parse_mode() -> None:
    # html.escape применяется, только когда parse_mode явно None
    class EscSG(StatesGroup):
        only = State()

    dp = Dispatcher()
    dp.include(
        Dialog(Window(Const("<b>жирный</b>"), state=EscSG.only, parse_mode=None)),
    )

    html = await render_preview_content(dp)

    assert "&lt;b&gt;" in html


async def test_render_preview_keeps_markup_with_parse_mode() -> None:
    class RawSG(StatesGroup):
        only = State()

    dp = Dispatcher()
    dp.include(Dialog(Window(Const("<b>жирный</b>"), state=RawSG.only)))

    html = await render_preview_content(dp)

    assert "<b>жирный</b>" in html


async def test_render_dialog_collects_all_windows() -> None:
    manager = FakeManager()
    dialog = make_dialog()

    rendered = await render_dialog(
        manager=manager,
        group=SG,
        dialog=dialog,
        simulate_events=False,
    )

    assert rendered.state_group == "SG"
    assert len(rendered.windows) == 2
    assert rendered.windows[0].message == "Первое окно"
    assert rendered.windows[1].message == "Второе окно<br>с переносом"
    assert rendered.windows[0].photo == "https://example.com/pic.png"
    assert rendered.windows[0].text_input is None


async def test_render_dialog_simulates_input() -> None:
    manager = FakeManager()
    dialog = make_dialog()

    rendered = await render_dialog(
        manager=manager,
        group=SG,
        dialog=dialog,
        simulate_events=True,
    )

    keyboard = rendered.windows[0].keyboard
    assert keyboard
    assert all(isinstance(b, RenderButton) for row in keyboard for b in row)


async def test_render_preview_writes_file(tmp_path: Path) -> None:
    target = tmp_path / "preview.html"

    await render_preview(make_router(), str(target))

    assert "Первое окно" in target.read_text(encoding="utf-8")


async def test_fake_manager_next_and_back() -> None:
    manager = FakeManager()
    dialog = make_dialog()
    manager.set_dialog(dialog)
    manager.set_state(SG.first)

    await manager.next()
    assert manager.current_context().state == SG.second

    await manager.back()
    assert manager.current_context().state == SG.first


async def test_fake_manager_next_beyond_last_state() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())
    manager.set_state(SG.second)

    with pytest.raises(ValueError, match="non-existent state"):
        await manager.next()


async def test_fake_manager_back_before_first_state() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())
    manager.set_state(SG.first)

    with pytest.raises(ValueError, match="non-existent state"):
        await manager.back()


async def test_fake_manager_context_lifecycle() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    assert manager.is_preview() is True
    assert manager.has_context() is True
    assert manager.dialog_data == {}
    assert manager.start_data == {}
    assert await manager.load_data() == {}
    assert manager.current_stack() is not None
    assert manager.show_mode is ShowMode.AUTO

    manager.show_mode = ShowMode.EDIT  # сеттер - no-op
    assert manager.show_mode is ShowMode.AUTO

    manager._context = None
    assert manager.has_context() is False
    with pytest.raises(NoContextError):
        manager.current_context()


async def test_fake_manager_no_op_methods() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    await manager.show()
    await manager.update()
    await manager.mark_closed()
    await manager.answer_callback()
    await manager.close_manager()
    assert manager.bg() is manager

    async with manager.fg() as fg_manager:
        assert fg_manager is manager


async def test_fake_manager_start_done_and_reset() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    await manager.start(SG.second)
    assert manager.current_context().state == SG.second

    await manager.done()
    assert manager.current_context().state._state == "-"

    await manager.reset_stack()
    assert manager.current_context().dialog_data == {}


async def test_fake_manager_find() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())
    manager.set_state(SG.first)

    assert manager.find("btn") is not None
    assert manager.find("missing") is None


async def test_fake_manager_show_raw() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())
    manager.set_state(SG.first)

    message = await manager.show_raw()

    assert message.text == "Первое окно"


def test_fake_manager_middleware_data_and_event() -> None:
    manager = FakeManager()
    data: dict[Any, Any] = manager.middleware_data

    assert manager.event is not None
    assert data


def test_create_photo_media_id() -> None:
    media_id = MediaId(token="tok")  # noqa: S106
    media = MediaAttachment(type=AttachmentType.IMAGE, media_id=media_id)

    assert create_photo(media) == str(media_id)


def test_create_photo_without_any_source() -> None:
    media = MediaAttachment(type=AttachmentType.IMAGE, url="http://e.com/a.png")
    media.url = None

    assert create_photo(media) is None


async def test_create_button_swallows_handler_error() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    dialog = MagicMock()
    dialog._callback_handler = AsyncMock(side_effect=RuntimeError("boom"))

    button = await create_button(
        title="Кнопка",
        callback="btn",
        manager=manager,
        state=SG.first,
        dialog=dialog,
        simulate_events=True,
    )

    assert button.title == "Кнопка"
    assert button.state == SG.first.state


async def test_render_input_returns_none_without_simulation() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    result = await render_input(
        manager=manager,
        state=SG.first,
        dialog=make_dialog(),
        content_type=AttachmentType.TEXT,
        simulate_events=False,
    )

    assert result is None


async def test_render_input_swallows_handler_error() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())
    manager.set_state(SG.first)

    dialog = MagicMock()
    dialog._message_handler = AsyncMock(side_effect=RuntimeError("boom"))

    # состояние не поменялось - инпут не отрисовывается
    assert (
        await render_input(
            manager=manager,
            state=SG.first,
            dialog=dialog,
            content_type=AttachmentType.TEXT,
            simulate_events=True,
        )
        is None
    )


async def test_render_input_when_state_changed() -> None:
    manager = FakeManager()
    manager.set_dialog(make_dialog())

    async def switch(*_args: Any, **_kwargs: Any) -> None:
        manager.set_state(SG.second)

    dialog = MagicMock()
    dialog._message_handler = AsyncMock(side_effect=switch)

    result = await render_input(
        manager=manager,
        state=SG.first,
        dialog=dialog,
        content_type=AttachmentType.TEXT,
        simulate_events=True,
    )

    assert result is not None
    assert result.title == AttachmentType.TEXT
    assert result.state == SG.second.state


async def test_render_reply_keyboard() -> None:
    manager = FakeManager()
    dialog = make_dialog()
    manager.set_dialog(dialog)

    button = CallbackButton(text=join_reply_callback("Текст", "payload"), payload="p")

    keyboard = await render_reply_keyboard(
        state=SG.first,
        reply_markup=[[button]],
        manager=manager,
        dialog=dialog,
        simulate_events=False,
    )

    assert keyboard[0][0].title == "Текст"


async def test_render_preview_list_group_row_gets_dialog() -> None:
    dialogs: list[DialogProtocol] = []

    def when(data: dict[Any, Any], widget: object, manager: DialogManager) -> bool:
        assert isinstance(manager, SubManager)
        dialogs.append(manager.dialog())
        return True

    dialog = Dialog(
        Window(
            Const("Список"),
            ListGroup(
                Button(Const("Элемент"), id="item", when=when),
                id="list",
                items=["a"],
                item_id_getter=lambda item: item,
            ),
            state=SG.first,
        ),
        Window(Const("Второе окно"), state=SG.second),
    )
    dp = Dispatcher()
    dp.include(dialog)

    await render_preview_content(dp)

    assert dialogs == [dialog]
