from unittest.mock import AsyncMock, Mock

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    DialogProtocol,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.manager.sub_manager import SubManager
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import ListGroup
from maxo.dialogs.widgets.kbd.button import Button, Url
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import (
    Callback,
    CallbackButton,
    LinkButton,
    MessageCallback,
    MessageCreated,
    User,
)
from tests.constants import NOW


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


async def test_get_page_count_without_pagination(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    page_count = await list_group.get_page_count({}, mock_manager)

    assert page_count == 1


async def test_get_page_count_with_pagination(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=2,
    )

    page_count = await list_group.get_page_count({}, mock_manager)

    assert page_count == 3


async def test_render_with_pagination(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Format("Button {item}"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=2,
    )

    keyboard = await list_group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 2
    assert keyboard[0][0].text == "Button a"
    assert keyboard[1][0].text == "Button b"


async def test_render_with_pagination_second_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Format("Button {item}"), "button"),
        id="list",
        items=["a", "b", "c", "d", "e"],
        item_id_getter=lambda item: item,
        page_size=2,
    )

    await list_group.set_page(Mock(), 1, mock_manager)
    keyboard = await list_group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 2
    assert keyboard[0][0].text == "Button c"
    assert keyboard[1][0].text == "Button d"


async def test_find_widget() -> None:
    button = Button(Const("Button"), "button")
    list_group = ListGroup(
        button,
        id="list",
        items=["a"],
        item_id_getter=lambda item: item,
    )

    widget = list_group.find("list")
    assert widget == list_group

    widget = list_group.find("button")
    assert widget == button

    widget = list_group.find("nonexistent")
    assert widget is None


async def test_process_item_callback(mock_manager: DialogManager) -> None:
    on_click = AsyncMock()
    button = Button(Const("Button"), "button", on_click=on_click)
    list_group = ListGroup(
        button,
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    fake_user = User(
        user_id=1,
        is_bot=False,
        first_name="Test",
        last_activity_time=NOW,
    )
    callback = MessageCallback(
        timestamp=NOW,
        callback=Callback(
            callback_id="1",
            user=fake_user,
            timestamp=NOW,
            payload="list:a:button",
        ),
    )

    result = await list_group._process_item_callback(
        callback,
        "a:button",
        Mock(),
        mock_manager,
    )

    assert result is True
    on_click.assert_called_once()


async def test_get_and_set_page(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
    )

    page = await list_group.get_page(mock_manager)
    assert page == 0

    await list_group.set_page(Mock(), 2, mock_manager)
    page = await list_group.get_page(mock_manager)
    assert page == 2


async def test_on_page_changed(mock_manager: DialogManager) -> None:
    on_page_changed = AsyncMock()
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
        page_size=1,
        on_page_changed=on_page_changed,
    )

    await list_group.set_page(Mock(), 1, mock_manager)

    on_page_changed.assert_called_once()


async def test_managed_list_group(mock_manager: DialogManager) -> None:
    list_group = ListGroup(
        Button(Const("Button"), "button"),
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    managed = list_group.managed(mock_manager)

    assert managed.widget == list_group
    assert managed.manager == mock_manager


async def test_managed_find_for_item(mock_manager: DialogManager) -> None:
    button = Button(Const("Button"), "button")
    list_group = ListGroup(
        button,
        id="list",
        items=["a", "b", "c"],
        item_id_getter=lambda item: item,
    )

    managed = list_group.managed(mock_manager)
    managed_button = managed.find_for_item("button", "a")

    assert managed_button is not None


class ListGroupSG(StatesGroup):
    main = State()


async def test_callback_manager_has_dialog_outside_and_inside_list_group() -> None:
    calls: list[tuple[DialogProtocol, bool]] = []

    async def on_click(
        event: MessageCallback,
        button: Button,
        manager: DialogManager,
    ) -> None:
        calls.append((manager.dialog(), isinstance(manager, SubManager)))

    async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
        await dialog_manager.start(ListGroupSG.main, mode=StartMode.RESET_STACK)

    dialog = Dialog(
        Window(
            Const("stub"),
            Button(Const("Top"), id="top", on_click=on_click),
            ListGroup(
                Button(Const("Item"), id="item", on_click=on_click),
                id="list",
                items=["a"],
                item_id_getter=lambda item: item,
            ),
            state=ListGroupSG.main,
        ),
    )
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp.include(dialog)
    dp.message_created.handler(start, CommandStart())
    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager)
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    await client.click(message_manager.one_message(), InlineButtonTextLocator("Top"))
    await client.click(message_manager.last_message(), InlineButtonTextLocator("Item"))

    assert calls == [(dialog, False), (dialog, True)]
