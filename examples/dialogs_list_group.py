"""
Диалог со списком элементов (ListGroup): кнопки по одному на каждый item из getter;
при клике сохраняем item_id в dialog_data и переходим в окно детали.
Запуск: python examples/dialogs_list_group.py
"""

import logging
import os
from typing import Any

from maxo import Bot, Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.widgets.kbd import Back, Button, ListGroup
from maxo.dialogs.widgets.text import Const, Format
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.types import MessageCallback, MessageCreated


class ListSG(StatesGroup):
    menu = State()
    detail = State()


ITEMS = [
    {"id": "apple", "name": "Яблоко", "price": "50"},
    {"id": "pear", "name": "Груша", "price": "60"},
    {"id": "melon", "name": "Дыня", "price": "100"},
]


async def get_items(**__: Any) -> dict[str, Any]:
    return {"items": ITEMS}


async def get_detail(dialog_manager: DialogManager, **__: Any) -> dict[str, Any]:
    selected_id = dialog_manager.dialog_data.get("selected_id", "")
    item = {"name": "", "price": ""}
    for i in ITEMS:
        if i["id"] == selected_id:
            item = i
            break
    return {"name": item["name"], "price": item["price"]}


async def on_item_click(
    _: MessageCallback,
    __: Button,
    manager: DialogManager,
) -> None:
    # В ListGroup manager приходит как SubManager с полем item_id
    manager.dialog_data["selected_id"] = getattr(manager, "item_id", "")
    await manager.next()


# ListGroup: кнопка на каждый item из getter; item_id_getter задаёт id для payload
list_dialog = Dialog(
    Window(
        Const("Выбери товар:"),
        ListGroup(
            Button(
                Format("{item[name]} - {item[price]} ₽"),
                id="i",
                on_click=on_item_click,
            ),
            id="products",
            item_id_getter=lambda x: x["id"],
            items=lambda d: d["items"],
        ),
        state=ListSG.menu,
        getter=get_items,
    ),
    Window(
        Format("Товар: {name}, цена {price} ₽"),
        Back(Const("← Назад")),
        getter=get_detail,
        state=ListSG.detail,
    ),
)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(ListSG.menu, mode=StartMode.RESET_STACK)


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
    dp.include(list_dialog)
    dp.message_created.handler(start, CommandStart())

    setup_dialogs(dp, events_isolation=events_isolation)
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
