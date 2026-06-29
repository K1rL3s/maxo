from unittest.mock import AsyncMock

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Button, Group
from maxo.dialogs.widgets.text import Const
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.updates import MessageCreated


async def test_render_group(mock_manager: DialogManager) -> None:
    group = Group(
        Button(Const("1"), id="first"),
        Button(Const("2"), id="second"),
        Button(Const("3"), id="third"),
    )

    keyboard = await group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 3

    assert len(keyboard[0]) == 1
    assert keyboard[0][0].text == "1"

    assert len(keyboard[1]) == 1
    assert keyboard[1][0].text == "2"

    assert len(keyboard[2]) == 1
    assert keyboard[2][0].text == "3"


async def test_render_group_with_width(mock_manager: DialogManager) -> None:
    group = Group(
        Button(Const("1"), id="first"),
        Button(Const("2"), id="second"),
        Button(Const("3"), id="third"),
        Button(Const("4"), id="fourth"),
        Button(Const("5"), id="fifth"),
        width=3,
    )

    keyboard = await group.render_keyboard(data={}, manager=mock_manager)

    assert len(keyboard) == 2

    assert len(keyboard[0]) == 3
    assert keyboard[0][0].text == "1"
    assert keyboard[0][1].text == "2"
    assert keyboard[0][2].text == "3"

    assert len(keyboard[1]) == 2
    assert keyboard[1][0].text == "4"
    assert keyboard[1][1].text == "5"


class MainSG(StatesGroup):
    start = State()


on_click_first_button = AsyncMock()
on_click_third_button = AsyncMock()


dialog = Dialog(
    Window(
        Const("stub"),
        Group(
            Button(Const("1"), id="first", on_click=on_click_first_button),
            Button(Const("2"), id="second"),
            Button(Const("3"), id="third", on_click=on_click_third_button),
        ),
        state=MainSG.start,
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def test_click_buttons_in_group() -> None:
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

    # start
    await client.send("/start")
    message = message_manager.one_message()

    # click first button
    await client.click(
        message,
        InlineButtonTextLocator("1"),
    )
    on_click_first_button.assert_called_once()

    # click third button
    await client.click(
        message,
        InlineButtonTextLocator("3"),
    )
    on_click_third_button.assert_called_once()
