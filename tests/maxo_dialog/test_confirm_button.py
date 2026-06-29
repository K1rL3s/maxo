from typing import Any
from unittest.mock import MagicMock

from maxo import Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.internal import PAYLOAD_KEY
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.widgets.kbd import ConfirmButton, SwitchTo
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.signals import AfterStartup, BeforeStartup
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.types import Message


class OrderSG(StatesGroup):
    pizza = State()
    sushi = State()


async def on_pizza(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_pizza"](callback.id)


async def on_pizza_cancel(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_pizza_cancel"](callback.id)


async def on_sushi(
    callback: MessageCallback,
    _: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.middleware_data["on_sushi"](callback.id)


confirm_dialog = Dialog(
    Window(
        Const("Пицца"),
        ConfirmButton(
            primary_text=Const("Заказать пиццу"),
            confirm_text=Const("Точно"),
            cancel_text=Const("Передумал"),
            warning_text=Const("Подтверди заказ пиццы"),
            on_confirm=on_pizza,
            on_cancel=on_pizza_cancel,
            id="pizza",
        ),
        SwitchTo(Const("К сушам"), state=OrderSG.sushi, id="to_sushi"),
        state=OrderSG.pizza,
    ),
    Window(
        Const("Суши"),
        ConfirmButton(
            primary_text=Const("Заказать суши"),
            confirm_text=Const("Точно суши"),
            cancel_text=Const("Передумал, не суши"),
            warning_text=None,
            on_confirm=on_sushi,
            on_cancel=None,
            id="sushi",
        ),
        SwitchTo(Const("К пиццам"), state=OrderSG.pizza, id="to_pizza"),
        state=OrderSG.sushi,
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(OrderSG.pizza, mode=StartMode.RESET_STACK)


def _assert_keyboard(message: Message, *buttons: tuple[str, ...]) -> None:
    keyboard = message.body.keyboard
    assert keyboard
    assert len(keyboard.buttons) == len(buttons)

    for i, row in enumerate(buttons):
        assert len(keyboard.buttons[i]) == len(row)
        for button, text in zip(keyboard.buttons[i], row, strict=True):
            assert button.text == text


async def test_click() -> None:
    on_pizza_mock = MagicMock()
    on_pizza_cancel_mock = MagicMock()
    on_sushi_mock = MagicMock()

    key_builder = DefaultKeyBuilder(with_destiny=True)
    event_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=JsonMemoryStorage(),
        events_isolation=event_isolation,
        key_builder=key_builder,
        workflow_data={
            "on_pizza": on_pizza_mock,
            "on_pizza_cancel": on_pizza_cancel_mock,
            "on_sushi": on_sushi_mock,
        },
    )
    dp.include(confirm_dialog)
    dp.message_created.handler(start, CommandStart())

    client = BotClient(dp)
    message_manager = MockMessageManager()
    setup_dialogs(dp, message_manager=message_manager, events_isolation=event_isolation)

    await dp.feed_signal(BeforeStartup(), client.bot)
    await dp.feed_signal(AfterStartup(), client.bot)

    await client.send("/start")
    dialog_message = message_manager.one_message()
    assert dialog_message.body.text == "Пицца"
    _assert_keyboard(dialog_message, ("Заказать пиццу",), ("К сушам",))

    # Проверка отмены
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать пиццу"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(
        dialog_message,
        ("Подтверди заказ пиццы",),
        ("Передумал", "Точно"),
        ("К сушам",),
    )

    message_manager.reset_history()
    cancel_id = await client.click(dialog_message, InlineButtonTextLocator("Передумал"))
    on_pizza_cancel_mock.assert_called_once_with(cancel_id)
    on_pizza_mock.assert_not_called()
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать пиццу",), ("К сушам",))

    # Проверка подтверждения
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать пиццу"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(
        dialog_message,
        ("Подтверди заказ пиццы",),
        ("Передумал", "Точно"),
        ("К сушам",),
    )

    message_manager.reset_history()
    confirm_id = await client.click(dialog_message, InlineButtonTextLocator("Точно"))
    on_pizza_mock.assert_called_once_with(confirm_id)
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать пиццу",), ("К сушам",))

    # Переходим к сушам
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("К сушам"))
    dialog_message = message_manager.one_message()
    assert dialog_message.body.text == "Суши"
    _assert_keyboard(dialog_message, ("Заказать суши",), ("К пиццам",))

    # Проверка отмены
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать суши"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(
        dialog_message,
        ("Передумал, не суши", "Точно суши"),
        ("К пиццам",),
    )

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Передумал, не суши"))
    on_sushi_mock.assert_not_called()
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать суши",), ("К пиццам",))

    # Проверка подтверждения
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать суши"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(
        dialog_message,
        ("Передумал, не суши", "Точно суши"),
        ("К пиццам",),
    )

    message_manager.reset_history()
    confirm_id = await client.click(
        dialog_message,
        InlineButtonTextLocator("Точно суши"),
    )
    on_sushi_mock.assert_called_once_with(confirm_id)
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать суши",), ("К пиццам",))

    # Проверка сброса между свитчами
    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("Заказать суши"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(
        dialog_message,
        ("Передумал, не суши", "Точно суши"),
        ("К пиццам",),
    )

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("К пиццам"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать пиццу",), ("К сушам",))

    message_manager.reset_history()
    await client.click(dialog_message, InlineButtonTextLocator("К сушам"))
    dialog_message = message_manager.one_message()
    _assert_keyboard(dialog_message, ("Заказать суши",), ("К пиццам",))


async def test_render_flags() -> None:
    manager_mock = MagicMock()
    manager_mock.middleware_data = {PAYLOAD_KEY: "id:__wait__"}

    button = ConfirmButton(
        id="id",
        primary_text=Const("Primary"),
        confirm_text=Const("Confirm"),
        cancel_text=Const("Cancel"),
        confirm_first=False,
        oneline=True,
    )
    keyboard = await button.render_keyboard({}, manager_mock)
    assert len(keyboard) == 1
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "Cancel"
    assert keyboard[0][1].text == "Confirm"

    button = ConfirmButton(
        id="id",
        primary_text=Const("Primary"),
        confirm_text=Const("Confirm"),
        cancel_text=Const("Cancel"),
        confirm_first=False,
        oneline=False,
    )
    keyboard = await button.render_keyboard({}, manager_mock)
    assert len(keyboard) == 2
    assert len(keyboard[0]) == 1
    assert len(keyboard[1]) == 1
    assert keyboard[0][0].text == "Cancel"
    assert keyboard[1][0].text == "Confirm"

    button = ConfirmButton(
        id="id",
        primary_text=Const("Primary"),
        confirm_text=Const("Confirm"),
        cancel_text=Const("Cancel"),
        confirm_first=True,
        oneline=True,
    )
    keyboard = await button.render_keyboard({}, manager_mock)
    assert len(keyboard) == 1
    assert len(keyboard[0]) == 2
    assert keyboard[0][0].text == "Confirm"
    assert keyboard[0][1].text == "Cancel"

    button = ConfirmButton(
        id="id",
        primary_text=Const("Primary"),
        confirm_text=Const("Confirm"),
        cancel_text=Const("Cancel"),
        confirm_first=True,
        oneline=False,
    )
    keyboard = await button.render_keyboard({}, manager_mock)
    assert len(keyboard) == 2
    assert len(keyboard[0]) == 1
    assert len(keyboard[1]) == 1
    assert keyboard[0][0].text == "Confirm"
    assert keyboard[1][0].text == "Cancel"
