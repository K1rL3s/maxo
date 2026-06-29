# FSM + Router: состояния анкеты, state.update_data/get_value,
# delete_message перед ответом

import logging
import os

from magic_filter import F

from maxo import Bot, Dispatcher, Router
from maxo.enums import TextFormat
from maxo.fsm import FSMContext, State, StateFilter, StatesGroup
from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

router = Router(__name__)


class UserRegistrationStatesGroup(StatesGroup):
    INPUT_NAME = State()
    INPUT_AGE = State()


@router.message_created(CommandStart())
async def start_handler(update: MessageCreated, state: FSMContext) -> None:
    await update.reply_text("Привет. Заполни анкету.")
    await update.answer_text("Введи имя.")
    await state.set_state(UserRegistrationStatesGroup.INPUT_NAME)


@router.message_created(
    MagicFilter(F.message.body.text)
    & StateFilter(UserRegistrationStatesGroup.INPUT_NAME),
)
async def input_name_handler(update: MessageCreated, state: FSMContext) -> None:
    await update.delete_message()

    text = update.message.body.text
    if text is None:
        await update.answer_text("Отправь текстовое сообщение")
        return

    await update.reply_text("Теперь отправь возраст")
    await update.answer_text(
        f"Анкета:\n<b>Имя</b>: {text}\n<b>Возраст</b>: отсутствует\n",
        format=TextFormat.HTML,
    )

    await state.update_data(name=text)
    await state.set_state(UserRegistrationStatesGroup.INPUT_AGE)


@router.message_created(
    MagicFilter(F.message.body.text)
    & StateFilter(UserRegistrationStatesGroup.INPUT_AGE),
)
async def input_age_handler(update: MessageCreated, state: FSMContext) -> None:
    await update.delete_message()

    text = update.message.body.text
    if text is None:
        await update.answer_text("Отправь текстовое сообщение")
        return

    try:
        age = int(text)
    except ValueError:
        await update.answer_text("Ты отправил не возраст. Попробуй еще раз")
        return

    name = await state.get_value("name")

    await update.answer_text("Ты успешно заполнил анкету")
    await update.answer_text(
        f"Анкета:\n<b>Имя</b>: {name}\n<b>Возраст</b>: {age}\n",
        format=TextFormat.HTML,
    )

    await state.clear()


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    bot = Bot(os.environ["TOKEN"])
    dp = Dispatcher()

    dp.include(router)

    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
