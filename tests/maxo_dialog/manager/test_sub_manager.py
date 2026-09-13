from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from maxo.dialogs.api.entities import Context, ShowMode, StartMode
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.manager.sub_manager import SubManager
from maxo.fsm.state import State, StatesGroup


class TestStates(StatesGroup):
    first = State()
    second = State()


@pytest.fixture
def mock_manager() -> MagicMock:
    manager = MagicMock(spec=DialogManager)
    manager.event = MagicMock()
    manager.middleware_data = {"ctx": {}}
    manager.start_data = {"initial": "data"}

    context = Context(
        dialog_data={"key": "value"},
        start_data={"initial": "data"},
        widget_data={},
        state=TestStates.first,
        _stack_id="_stack_id",
        _intent_id="_intent_id",
    )
    manager.current_context = Mock(return_value=context)
    manager.has_context = Mock(return_value=True)
    manager.is_preview = Mock(return_value=False)
    manager.current_stack = Mock(return_value=MagicMock())

    manager.close_manager = AsyncMock()
    manager.show = AsyncMock()
    manager.answer_callback = AsyncMock()
    manager.reset_stack = AsyncMock()
    manager.load_data = AsyncMock(return_value={"loaded": "data"})
    manager.find = Mock(return_value=None)
    manager.next = AsyncMock()
    manager.back = AsyncMock()
    manager.done = AsyncMock()
    manager.mark_closed = AsyncMock()
    manager.start = AsyncMock()
    manager.switch_to = AsyncMock()
    manager.bg = Mock(return_value=MagicMock())

    manager.show_mode = ShowMode.AUTO

    return manager


@pytest.fixture
def mock_widget() -> MagicMock:
    widget = MagicMock()
    widget.find = Mock(return_value=None)
    return widget


async def test_init(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(
        widget=mock_widget,
        manager=mock_manager,
        widget_id="widget_1",
        item_id="item_1",
    )

    assert sub.widget is mock_widget
    assert sub.manager is mock_manager
    assert sub.widget_id == "widget_1"
    assert sub.item_id == "item_1"


async def test_event_property(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.event is mock_manager.event


async def test_middleware_data_property(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.middleware_data is mock_manager.middleware_data


async def test_dialog_data_property(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    # dialog_data вызывает current_context().dialog_data
    assert sub.dialog_data == {"key": "value"}


async def test_start_data_property(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.start_data == {"initial": "data"}


async def test_current_context(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    context = sub.current_context()

    # Проверяем, что создается изолированный контекст с widget_data
    assert isinstance(context, Context)
    assert context.dialog_data == {"key": "value"}
    assert context.widget_data == {}

    # Второй вызов должен создать структуру widget_data
    _ = sub.current_context()
    parent_context = mock_manager.current_context()
    assert "widget_1" in parent_context.widget_data
    assert "item_1" in parent_context.widget_data["widget_1"]


async def test_has_context(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.has_context() is True


async def test_is_preview(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.is_preview() is False


async def test_current_stack(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.current_stack() is mock_manager.current_stack()


async def test_close_manager(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.close_manager()
    mock_manager.close_manager.assert_called_once()


async def test_show(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.show(ShowMode.EDIT)
    mock_manager.show.assert_called_once_with(ShowMode.EDIT)


async def test_answer_callback(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.answer_callback()
    mock_manager.answer_callback.assert_called_once()


async def test_reset_stack(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.reset_stack(remove_keyboard=False)
    mock_manager.reset_stack.assert_called_once_with(False)


async def test_load_data(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    data = await sub.load_data()
    assert data == {"loaded": "data"}


async def test_find_widget_not_found(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    found = sub.find("nonexistent")
    assert found is None


async def test_find_widget_found(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    found_widget = MagicMock()
    managed_widget = MagicMock()
    found_widget.managed = Mock(return_value=managed_widget)

    mock_widget.find = Mock(return_value=found_widget)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    result = sub.find("existing_widget")

    assert result is managed_widget
    found_widget.managed.assert_called_once_with(sub)


async def test_find_in_parent(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    parent_widget = MagicMock()
    mock_manager.find = Mock(return_value=parent_widget)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    result = sub.find_in_parent("parent_widget")

    assert result is parent_widget
    mock_manager.find.assert_called_once_with("parent_widget")


async def test_show_mode_getter(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    assert sub.show_mode == ShowMode.AUTO


async def test_show_mode_setter(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    sub.show_mode = ShowMode.EDIT
    assert mock_manager.show_mode == ShowMode.EDIT


async def test_next(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.next(ShowMode.SEND)
    mock_manager.next.assert_called_once_with(ShowMode.SEND)


async def test_back(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.back(ShowMode.DELETE_AND_SEND)
    mock_manager.back.assert_called_once_with(ShowMode.DELETE_AND_SEND)


async def test_done(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.done(result={"result": "data"}, show_mode=ShowMode.EDIT)
    mock_manager.done.assert_called_once_with({"result": "data"}, ShowMode.EDIT)


async def test_mark_closed(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.mark_closed()
    mock_manager.mark_closed.assert_called_once()


async def test_start(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.start(
        state=TestStates.second,
        data={"start": "data"},
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )
    mock_manager.start.assert_called_once_with(
        state=TestStates.second,
        data={"start": "data"},
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
        access_settings=None,
    )


async def test_switch_to(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.switch_to(TestStates.second, ShowMode.EDIT)
    mock_manager.switch_to.assert_called_once_with(TestStates.second, ShowMode.EDIT)


async def test_update_with_data(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.update(data={"new_key": "new_value"}, show_mode=ShowMode.EDIT)

    context = sub.current_context()
    assert context.dialog_data["new_key"] == "new_value"
    mock_manager.show.assert_called_once_with(ShowMode.EDIT)


async def test_update_without_data(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    await sub.update(show_mode=ShowMode.EDIT)
    mock_manager.show.assert_called_once_with(ShowMode.EDIT)


async def test_bg(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    bg_manager = MagicMock()
    mock_manager.bg = Mock(return_value=bg_manager)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")
    result = sub.bg(user_id=123, chat_id=456, stack_id="stack_1", load=True)

    assert result is bg_manager
    mock_manager.bg.assert_called_once_with(
        user_id=123,
        chat_id=456,
        stack_id="stack_1",
        load=True,
    )


async def test_fg_context_manager(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")

    async with sub.fg() as manager:
        assert manager is sub


async def test_dialog(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    dialog = MagicMock()
    mock_manager.dialog = Mock(return_value=dialog)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")

    assert sub.dialog() is dialog


async def test_storage(mock_widget: MagicMock, mock_manager: MagicMock) -> None:
    storage = MagicMock()
    mock_manager.storage = Mock(return_value=storage)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")

    assert sub.storage() is storage


async def test_is_event_simulated(
    mock_widget: MagicMock,
    mock_manager: MagicMock,
) -> None:
    mock_manager.is_event_simulated = Mock(return_value=True)

    sub = SubManager(mock_widget, mock_manager, "widget_1", "item_1")

    assert sub.is_event_simulated() is True
