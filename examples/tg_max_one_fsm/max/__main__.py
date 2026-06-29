import asyncio
import logging
import os
from pathlib import Path

from magic_filter import F

from maxo import Bot, Dispatcher, Router
from maxo.fsm.context import FSMContext
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.state import State, StatesGroup
from maxo.fsm.storages.redis import RedisStorage
from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters import Command, CommandObject, CommandStart
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling
from maxo.types import CallbackButton

from ..ids import SharedId
from ..user_repo import DbUser, UserRepo
from .current_user import CurrentUserMiddleware
from .fsm_context import SharedFSMContextMiddleware

router = Router()


class MyStates(StatesGroup):
    state1 = State()
    state2 = State()


def get_keyboard() -> list[list[CallbackButton]]:
    return [
        [
            CallbackButton(text="Перейти в состояние 1", payload="to_state_1"),
            CallbackButton(text="Перейти в состояние 2", payload="to_state_2"),
        ],
        [
            CallbackButton(text="Очистить состояние", payload="clear_state"),
        ],
    ]


@router.message_created(CommandStart())
async def start_handler(
    message: MessageCreated,
    fsm_context: FSMContext,
    current_user: DbUser,
) -> None:
    current_state = await fsm_context.get_state()

    await message.send_message(
        (
            f"Ваш общий ID: {current_user.shared_id}\n\n"
            f"Отправьте эту команду боту TG: /link {current_user.shared_id}\n\n"
            "Или отправьте эту команду этому боту из другого аккаунта, "
            "чтобы связать их: /link <shared_id>"
        ),
    )
    await message.send_message(
        text=f"Ваше текущее состояние: {current_state}",
        keyboard=get_keyboard(),
    )


@router.message_created(Command("state"))
async def get_state_handler(message: MessageCreated, fsm_context: FSMContext) -> None:
    current_state = await fsm_context.get_state()
    await message.send_message(text=f"Ваше текущее состояние: {current_state}")


@router.message_created(Command("link"))
async def handle_deeplink(
    message: MessageCreated,
    command: CommandObject,
    user_repo: UserRepo,
    current_user: DbUser,
) -> None:
    try:
        shared_id_to_link = SharedId(int(command.args))
        await user_repo.link_accounts(
            current_user=current_user,
            shared_id_to_link=shared_id_to_link,
        )
        await message.send_message(text="Аккаунты успешно связаны!")
    except (IndexError, ValueError, TypeError):
        await message.send_message(text="Использование: /link <shared_id>")


@router.message_callback(MagicFilter(F.payload == "to_state_1"))
async def to_state_1(callback: MessageCallback, fsm_context: FSMContext) -> None:
    await fsm_context.set_state(MyStates.state1)
    current_state = await fsm_context.get_state()
    await callback.edit_message(
        text=f"Ваше текущее состояние: {current_state}",
        keyboard=get_keyboard(),
    )


@router.message_callback(MagicFilter(F.payload == "to_state_2"))
async def to_state_2(callback: MessageCallback, fsm_context: FSMContext) -> None:
    await fsm_context.set_state(MyStates.state2)
    current_state = await fsm_context.get_state()
    await callback.edit_message(
        text=f"Ваше текущее состояние: {current_state}",
        keyboard=get_keyboard(),
    )


@router.message_callback(MagicFilter(F.payload == "clear_state"))
async def clear_state(callback: MessageCallback, fsm_context: FSMContext) -> None:
    await fsm_context.clear()
    current_state = await fsm_context.get_state()
    await callback.edit_message(
        text=f"Состояние очищено. Ваше текущее состояние: {current_state}",
        keyboard=get_keyboard(),
    )


async def main() -> None:
    token = os.environ["MAX_TOKEN"]
    redis_url = os.environ["REDIS_URL"]

    db_path = (Path(__file__).parent.parent / "db.sqlite").resolve()
    user_repo = UserRepo(str(db_path))
    await user_repo.create_table()

    key_builder = DefaultKeyBuilder(prefix="fsm", separator=":", with_bot_id=False)
    storage = RedisStorage.from_url(url=redis_url, key_builder=key_builder)
    event_isolation = storage.create_isolation()
    dp = Dispatcher(
        key_builder=None,  # because use custom FSM
        storage=None,  # because use custom FSM
        events_isolation=None,  # because use custom FSM
        disable_fsm=True,  # because use custom FSM
        workflow_data={"user_repo": user_repo},
    )
    dp.update.middleware.outer(CurrentUserMiddleware())
    dp.update.middleware.outer(
        SharedFSMContextMiddleware(storage=storage, events_isolation=event_isolation),
    )
    dp.include(router)

    bot = Bot(token=token)
    polling = LongPolling(dp)
    await polling.start(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
