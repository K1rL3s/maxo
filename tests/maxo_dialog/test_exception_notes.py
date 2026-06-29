from unittest.mock import Mock

import pytest
from jinja2 import UndefinedError

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import ScrollingGroup, Select
from maxo.dialogs.widgets.text import Const, Jinja
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import CommandStart
from maxo.routing.signals import BeforeStartup
from maxo.routing.updates import MessageCreated


class MainSG(StatesGroup):
    start = State()


dialog = Dialog(
    Window(
        Const("stub"),
        ScrollingGroup(
            Select(
                Jinja("{{undefined + 1}}"),
                id="select_id",
                item_id_getter=lambda x: x,
                items="data",
            ),
            id="scrolling_group_id",
            width=1,
            height=10,
        ),
        state=MainSG.start,
        getter={"data": [{"foo": 1}]},
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


async def test_exception_notes() -> None:
    usecase = Mock()
    user_getter = Mock(side_effect=["Username"])
    dp = Dispatcher(
        workflow_data={"usecase": usecase, "user_getter": user_getter},
        storage=JsonMemoryStorage(),
    )
    dp.include_router(dialog)
    dp.message.register(start, CommandStart())

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(BeforeStartup(), client.bot)

    with pytest.raises(UndefinedError) as exc_info:
        await client.send("/start")

    assert exc_info.value.__notes__
    assert Jinja.__name__ in exc_info.value.__notes__[0]
    assert exc_info.value.__notes__[1:] == [
        "at <Select id=select_id>",
        "at <ScrollingGroup id=scrolling_group_id>",
        "maxo.dialogs state: <State 'MainSG:start'>",
    ]
