# Диалог - цепочка Window (окон) с виджетами (Text, Media, Input)

import logging
import os
from pathlib import Path
from typing import Any

from maxo import Bot, Dispatcher
from maxo.dialogs import (
    ChatEvent,
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.input import ManagedTextInput, MessageInput, TextInput
from maxo.dialogs.widgets.kbd import Back, Button, Row, Select, SwitchTo
from maxo.dialogs.widgets.media import StaticMedia
from maxo.dialogs.widgets.text import Const, Format, Multi
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling

BASE_DIR = Path(__file__).resolve().parent

key_builder = DefaultKeyBuilder(with_destiny=True)
dp = Dispatcher(key_builder=key_builder)


class DialogSG(StatesGroup):
    greeting = State()
    age = State()
    finish = State()


async def get_data(dialog_manager: DialogManager, **__: Any) -> dict[str, Any]:
    age = dialog_manager.dialog_data.get("age", None)
    return {
        "name": dialog_manager.dialog_data.get("name", ""),
        "age": age,
        "can_smoke": age in ("18-25", "25-40", "40+"),
    }


async def name_handler(
    message: MessageCreated,
    text_input: ManagedTextInput[str],
    dialog_manager: DialogManager,
    name: str,
) -> None:
    if dialog_manager.is_preview():
        await dialog_manager.next()
        return

    dialog_manager.dialog_data["name"] = name

    await message.answer_text(f"Привет, {name}")

    await dialog_manager.next()


async def other_type_handler(
    message: MessageCreated,
    message_input: MessageInput,
    dialog_manager: DialogManager,
) -> None:
    await message.answer_text("Ожидался текст")


async def on_finish(
    callback: MessageCallback,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    if dialog_manager.is_preview():
        await dialog_manager.done()
        return

    await callback.callback_answer("Спасибо. Чтобы начать заново - /start")

    await dialog_manager.done()


async def on_age_changed(
    callback: ChatEvent,
    select: Any,
    dialog_manager: DialogManager,
    item_id: str,
) -> None:
    dialog_manager.dialog_data["age"] = item_id
    await dialog_manager.next()


dialog = Dialog(
    Window(
        Const("Привет! Представься, пожалуйста:"),
        StaticMedia(path=BASE_DIR / "files" / "watermelon.jpg"),
        StaticMedia(path=BASE_DIR / "files" / "naked-watermelon.png"),
        TextInput(id="name_handler", on_success=name_handler),
        MessageInput(other_type_handler),
        state=DialogSG.greeting,
    ),
    Window(
        Format("{name}! Сколько тебе лет?"),
        Select(
            Format("{item}"),
            items=["0-12", "12-18", "18-25", "25-40", "40+"],
            item_id_getter=lambda x: x,
            id="w_age",
            on_click=on_age_changed,
        ),
        state=DialogSG.age,
        getter=get_data,
        preview_data={"name": "Tishka17"},
    ),
    Window(
        Multi(
            Format("{name}! Спасибо за ответы."),
            Const("Надеюсь, не куришь", when="can_smoke"),
            sep="\n\n",
        ),
        Row(
            Back(),
            SwitchTo(Const("Заново"), id="restart", state=DialogSG.greeting),
            Button(Const("Готово"), on_click=on_finish, id="finish"),
        ),
        getter=get_data,
        state=DialogSG.finish,
    ),
)


@dp.message_created(CommandStart())
async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    # StartMode.RESET_STACK: сброс стека при старте, пользователь с первого окна;
    # иначе возможен переход в уже идущий диалог с сохранённым стеком
    await dialog_manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(os.environ["TOKEN"])

    setup_dialogs(dp)
    dp.include(dialog)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
