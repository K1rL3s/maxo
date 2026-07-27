import logging
import os
from time import time
from typing import Any

from maxo import Bot, Dispatcher, Router
from maxo.dialogs import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.kbd import Back, Next, SwitchTo
from maxo.dialogs.widgets.text import Const, Format, Multi
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.types import MessageCreated


class StartSG(StatesGroup):
    first = State()
    second = State()
    third = State()


async def get_username(**__: Any) -> dict[str, Any]:
    return {"username": "друг"}


async def get_phone(**__: Any) -> dict[str, Any]:
    return {"phone": "+78005553535"}


# Getter подставляет данные в окно; SwitchTo/Back/Next - переходы между состояниями
start_dialog = Dialog(
    Window(
        Multi(Const("Привет,"), Format("{username} {phone}!"), sep=" "),
        Const("Как твои дела?"),
        SwitchTo(Const("Вперёд первый"), id="next", state=StartSG.second),
        Next(Const("Вперёд второй")),
        getter=[get_username, get_phone],
        state=StartSG.first,
    ),
    Window(
        Const("Второе окно"),
        Format("{phone}"),
        SwitchTo(Const("Назад первый"), id="back", state=StartSG.first),
        Back(Const("Назад второй")),
        getter=get_phone,
        state=StartSG.second,
    ),
)


start_router = Router(name=__name__)


@start_router.message_created()
async def start(
    message: MessageCreated,
    dialog_manager: DialogManager,
) -> None:
    # RESET_STACK - сброс стека при старте; data передаётся в диалог
    await dialog_manager.start(
        state=StartSG.first,
        show_mode=ShowMode.SEND,
        mode=StartMode.RESET_STACK,
        data={"time": time()},
    )


def main() -> None:
    bot = Bot(os.environ["TOKEN"])

    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = MemoryStorage(key_builder=key_builder)
    events_isolation = SimpleEventIsolation(key_builder=key_builder)

    dp = Dispatcher(
        storage=storage,
        events_isolation=events_isolation,
        key_builder=key_builder,
    )

    dp.include(start_router, start_dialog)
    setup_dialogs(dp, events_isolation=events_isolation)

    dp.run_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
