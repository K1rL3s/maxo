import asyncio
import logging
import os

from maxo import Bot, Dispatcher, Router
from maxo.dialogs import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.kbd import Button, ConfirmButton
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling


class SG(StatesGroup):
    main = State()


async def on_pizza(
    callback: MessageCallback,
    widget: ConfirmButton,
    manager: DialogManager,
) -> None:
    await callback.message.answer("Пицца заказана, жди курьера 🍕")
    manager.show_mode = ShowMode.SEND


async def on_pizza_cancel(
    callback: MessageCallback,
    widget: ConfirmButton,
    manager: DialogManager,
) -> None:
    await callback.message.answer("Пицца уже в печи, жаль =(")
    manager.show_mode = ShowMode.SEND


async def on_sushi(
    callback: MessageCallback,
    widget: ConfirmButton,
    manager: DialogManager,
) -> None:
    await callback.message.answer("Роллы заказаны, жди рыбу 🐡")
    manager.show_mode = ShowMode.SEND


confirm_dialog = Dialog(
    Window(
        Const("Нажми на любой заказ, чтобы посмотреть работу ConfirmButton"),
        ConfirmButton(
            primary_text=Const("🍕 Заказать пиццу"),
            confirm_text=Const("✅ Точно"),
            cancel_text=Const("❌ Передумал"),
            warning_text=Const("🍕 Подтверди заказ пиццы"),
            on_confirm=on_pizza,
            on_cancel=on_pizza_cancel,
            id="pizza",
        ),
        Button(Const("-"), id="empty"),
        ConfirmButton(
            primary_text=Const("🍣 Заказать суши"),
            confirm_text=Const("✅ Точно суши"),
            cancel_text=Const("❌ Передумал, не суши"),
            warning_text=None,
            on_confirm=on_sushi,
            on_cancel=None,
            id="sushi",
        ),
        state=SG.main,
    ),
)

router = Router()


@router.message_created(CommandStart())
async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(
        state=SG.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def main() -> None:
    bot = Bot(os.environ["TOKEN"], warming_up=not __debug__)

    key_builder = DefaultKeyBuilder(with_destiny=True)
    events_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=MemoryStorage(key_builder=key_builder),
        events_isolation=events_isolation,
        key_builder=key_builder,
    )

    dp.include(router, confirm_dialog)
    setup_dialogs(dp)

    await LongPolling(dp).start(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
