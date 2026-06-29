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
from maxo.dialogs.widgets.media.static import StaticMedia
from maxo.enums import AttachmentType
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.routing.filters import Command
from maxo.routing.updates import MessageCreated


class MainSG(StatesGroup):
    with_url = State()
    with_path = State()


dialog = Dialog(
    Window(
        StaticMedia(url="fake_image.png"),
        state=MainSG.with_url,
    ),
    Window(
        StaticMedia(path="fake_image.png"),
        state=MainSG.with_path,
    ),
)


async def start_url(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.with_url, mode=StartMode.RESET_STACK)


async def start_path(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(MainSG.with_path, mode=StartMode.RESET_STACK)


async def test_click() -> None:
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        key_builder=DefaultKeyBuilder(with_destiny=True),
    )
    dp.include(dialog)
    dp.message_created.handler(start_url, Command("url"))
    dp.message_created.handler(start_path, Command("path"))

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager)

    # with url parameter
    await client.send("/url")
    first_message = message_manager.one_message()
    assert first_message.body.attachments is not None
    assert any(a.type == AttachmentType.IMAGE for a in first_message.body.attachments)

    message_manager.reset_history()

    # with path parameter
    await client.send("/path")
    first_message = message_manager.one_message()
    assert first_message.body.attachments is not None
    assert any(a.type == AttachmentType.IMAGE for a in first_message.body.attachments)
