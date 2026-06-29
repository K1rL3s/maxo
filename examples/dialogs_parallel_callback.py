"""
Пример параллельной обработки callback в Dialog

Стандартный Dialog._callback_handler делает answer_callback() и show()
последовательно. На больших RTT (например, Россия<->Сингапур ~220ms) это даёт
лишнюю задержку - оба запроса независимы, можно параллелить

ParallelDialog ниже оверрайдит _callback_handler через asyncio.gather.
Семантика та же: если show() кидает исключение - оно пробрасывается,
как и в sequential варианте (gather по умолчанию не глотает)

Применять имеет смысл только если бот географически далеко от Max API
"""

import asyncio
import contextlib
import dataclasses
import logging
import os
from collections.abc import Awaitable
from typing import Any

from maxo import Bot, Dispatcher
from maxo.dialogs import (
    Dialog,
    DialogManager,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.protocols import CancelEventProcessing
from maxo.dialogs.utils import remove_intent_id
from maxo.dialogs.widgets.kbd import Button, Row, SwitchTo
from maxo.dialogs.widgets.text import Const
from maxo.errors import AttributeIsEmptyError
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.routing.ctx import Ctx
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCallback
from maxo.transport.long_polling import LongPolling


class ParallelDialog(Dialog):
    """Dialog с параллельным answer_callback + show через asyncio.gather."""

    async def _callback_handler(
        self,
        callback: MessageCallback,
        ctx: Ctx,
        dialog_manager: DialogManager,
    ) -> None:
        old_context = dialog_manager.current_context()
        _, payload = remove_intent_id(callback.callback.payload)

        cleaned_callback = dataclasses.replace(callback.callback, payload=payload)
        cleaned_event = dataclasses.replace(callback, callback=cleaned_callback)

        with contextlib.suppress(AttributeIsEmptyError):
            bot = callback.bot
            cleaned_callback.as_(bot)
            cleaned_event.as_(bot)
            if cleaned_event.message:
                cleaned_event.message.as_(bot)

        window = await self._current_window(dialog_manager)
        try:
            processed = await window.process_callback(
                cleaned_event,
                self,
                dialog_manager,
            )
        except CancelEventProcessing:
            processed = False

        tasks: list[Awaitable[Any]] = [dialog_manager.answer_callback()]
        if self._need_refresh(processed, old_context, dialog_manager):
            tasks.append(dialog_manager.show())
        await asyncio.gather(*tasks)


class DialogSG(StatesGroup):
    A = State()
    B = State()


async def on_ping(
    callback: MessageCallback,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    pongs = dialog_manager.dialog_data.get("pongs", 0)
    dialog_manager.dialog_data["pongs"] = pongs + 1


dialog = ParallelDialog(
    Window(
        Const("Окно A"),
        Row(
            Button(Const("Пинг"), id="ping", on_click=on_ping),
            SwitchTo(Const("Окно Б"), id="to_b", state=DialogSG.B),
        ),
        state=DialogSG.A,
    ),
    Window(
        Const("Окно Б"),
        SwitchTo(Const("Окно A"), id="to_a", state=DialogSG.A),
        state=DialogSG.B,
    ),
)


key_builder = DefaultKeyBuilder(with_destiny=True)
dp = Dispatcher(key_builder=key_builder)


@dp.message_created(CommandStart())
@dp.bot_started()
async def start(_: Any, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(DialogSG.A, mode=StartMode.RESET_STACK)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(os.environ["TOKEN"])

    setup_dialogs(dp)
    dp.include(dialog)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
