import importlib
import sys
from types import ModuleType
from typing import Any, ClassVar, Self, cast

import pytest

from maxo import Ctx, Dispatcher
from maxo.bot.bot import Bot
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import Back, Cancel, Group, Next, Start
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.types import Message, MessageCreated


class MainSG(StatesGroup):
    start = State()
    next = State()


class SecondarySG(StatesGroup):
    start = State()


class ToolsMainSG(StatesGroup):
    start = State()
    next = State()


class ToolsChildSG(StatesGroup):
    start = State()


async def start(
    message: MessageCreated,
    ctx: Ctx,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


@pytest.fixture
def dp(message_manager: MockMessageManager) -> Dispatcher:
    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
    )
    dp.message_created.handler(start, CommandStart())
    dp.include(
        Dialog(
            Window(
                Const("First"),
                Next(),
                Start(Const("Start"), state=SecondarySG.start, id="start"),
                Cancel(),
                state=MainSG.start,
            ),
            Window(
                Const("Second"),
                Back(),
                state=MainSG.next,
            ),
        ),
    )
    dp.include(
        Dialog(
            Window(
                Format("Subdialog"),
                Cancel(),
                state=SecondarySG.start,
            ),
        ),
    )
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)
    return dp


@pytest.fixture
def client(dp: Dispatcher) -> BotClient:
    return BotClient(dp)


@pytest.fixture
def bot() -> Bot:
    return FakeBot()


async def test_start(
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    # start
    await client.send("/start")
    first_message = message_manager.one_message()
    assert first_message.body.text == "First"
    assert first_message.body.keyboard


async def test_next_back(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # click next
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Next"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Second"

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Back"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.body.keyboard


async def test_finish_last(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # click back
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.body.keyboard, "Keyboard closed"


async def test_reset_stack(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    first_message: Message | None = None
    for _ in range(200):
        message_manager.reset_history()
        await client.send("/start")
        first_message = message_manager.one_message()
        assert first_message.body.text == "First"

    message_manager.reset_history()

    assert first_message is not None
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert not last_message.body.keyboard, "Keyboard closed"


@pytest.mark.flaky(reruns=2)
async def test_subdialog(
    dp: Dispatcher,
    bot: Bot,
    message_manager: MockMessageManager,
    client: BotClient,
) -> None:
    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    first_message = message_manager.one_message()

    # start subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        first_message,
        InlineButtonTextLocator("Start"),
    )
    message_manager.assert_answered(callback_id)
    second_message = message_manager.one_message()
    assert second_message.body.text == "Subdialog"

    # close subdialog
    message_manager.reset_history()
    callback_id = await client.click(
        second_message,
        InlineButtonTextLocator("Cancel"),
    )
    message_manager.assert_answered(callback_id)
    last_message = message_manager.one_message()
    assert last_message.body.text == "First"
    assert last_message.body.keyboard


class FakeContext:
    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class FakeNode:
    edges: ClassVar[list[tuple["FakeNode", "FakeNode"]]] = []

    def __init__(self, label: str, icon_path: str) -> None:
        self.label = label
        self.icon_path = icon_path

    def __rshift__(self, edge: object) -> "FakeConnector":
        return FakeConnector(self, edge)


class FakeConnector:
    def __init__(self, from_node: FakeNode, edge: object) -> None:
        self.from_node = from_node
        self.edge = edge

    def __rshift__(self, to_node: FakeNode) -> FakeNode:
        FakeNode.edges.append((self.from_node, to_node))
        return to_node


class FakeEdge:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs


def install_fake_diagrams(monkeypatch: pytest.MonkeyPatch) -> None:
    diagrams = ModuleType("diagrams")
    diagrams_module = cast(Any, diagrams)
    diagrams_module.Node = FakeNode
    diagrams_module.Edge = FakeEdge
    diagrams_module.Cluster = FakeContext
    diagrams_module.Diagram = FakeContext

    custom = ModuleType("diagrams.custom")
    custom_module = cast(Any, custom)
    custom_module.Custom = FakeNode

    monkeypatch.setitem(sys.modules, "diagrams", diagrams)
    monkeypatch.setitem(sys.modules, "diagrams.custom", custom)
    sys.modules.pop("maxo.dialogs.tools.transitions", None)


def test_render_transitions_with_fake_diagrams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeNode.edges.clear()
    install_fake_diagrams(monkeypatch)
    transitions = importlib.import_module("maxo.dialogs.tools.transitions")
    transition_dp = Dispatcher()
    transition_dp.include(
        Dialog(
            Window(
                Const("First"),
                Group(
                    Next(),
                    Start(Const("Start"), id="start", state=ToolsChildSG.start),
                    Cancel(),
                    id="group",
                ),
                state=ToolsMainSG.start,
            ),
            Window(Const("Second"), Back(), state=ToolsMainSG.next),
        ),
    )
    transition_dp.include(
        Dialog(Window(Const("Child"), Cancel(), state=ToolsChildSG.start)),
    )

    transitions.render_transitions(transition_dp)

    assert FakeNode.edges


def test_render_transitions_reports_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_fake_diagrams(monkeypatch)
    transitions = importlib.import_module("maxo.dialogs.tools.transitions")
    original_import_module = importlib.import_module

    def raise_import_error(name: str) -> ModuleType:
        if name == "diagrams":
            raise ImportError("missing diagrams")
        return original_import_module(name)

    monkeypatch.setattr(transitions.importlib, "import_module", raise_import_error)

    with pytest.raises(ImportError, match="Install maxo\\[preview\\]"):
        transitions.render_transitions(Dispatcher())
