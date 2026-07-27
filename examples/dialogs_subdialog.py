"""
Поддиалог: из главного меню кнопка открывает второй диалог (другой StatesGroup);
закрытие поддиалога (Cancel/done) возвращает в главное меню.
Запуск: python examples/dialogs_subdialog.py
"""

import logging
import os

from maxo import Bot, Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.kbd import Cancel, Start
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.types import MessageCreated


class MainSG(StatesGroup):
    menu = State()


class SettingsSG(StatesGroup):
    menu = State()


# Главное меню: кнопка «Настройки» запускает другой диалог (другой StatesGroup)
main_dialog = Dialog(
    Window(
        Const("Главное меню"),
        Start(Const("Настройки"), id="settings", state=SettingsSG.menu),
        state=MainSG.menu,
    ),
)

# Поддиалог: своя цепочка окон; Cancel (done) возвращает в вызывавший диалог
settings_dialog = Dialog(
    Window(
        Const("Настройки. Здесь можно что-то настроить."),
        Cancel(Const("← Назад")),
        state=SettingsSG.menu,
    ),
)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(os.environ["TOKEN"])
    key_builder = DefaultKeyBuilder(with_destiny=True)
    events_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=MemoryStorage(key_builder=key_builder),
        events_isolation=events_isolation,
        key_builder=key_builder,
    )

    @dp.message_created(CommandStart())
    async def start(_: MessageCreated, dialog_manager: DialogManager) -> None:
        await dialog_manager.start(MainSG.menu, mode=StartMode.RESET_STACK)

    dp.include(main_dialog, settings_dialog)
    setup_dialogs(dp, events_isolation=events_isolation)
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
