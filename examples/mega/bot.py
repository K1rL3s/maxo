import asyncio
import logging
import os

from bot_dialogs import states
from bot_dialogs.about import about_dialog
from bot_dialogs.calendar import calendar_dialog
from bot_dialogs.counter import counter_dialog
from bot_dialogs.layouts import layouts_dialog
from bot_dialogs.link_preview import link_preview_dialog
from bot_dialogs.main import main_dialog
from bot_dialogs.multi_widget import multiwidget_dialog
from bot_dialogs.scrolls import scroll_dialog
from bot_dialogs.select import selects_dialog
from bot_dialogs.switch import switch_dialog
from magic_filter import F

from maxo import Bot, Dispatcher, Router
from maxo.dialogs import DialogManager, ShowMode, StartMode, setup_dialogs
from maxo.dialogs.api.exceptions import UnknownIntent
from maxo.errors import MaxBotApiError
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage
from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters import ExceptionTypeFilter
from maxo.routing.updates import ErrorEvent, MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling

logger = logging.getLogger(__name__)


async def start(message: MessageCreated, dialog_manager: DialogManager) -> None:
    # it is important to reset stack because user wants to restart everything
    await dialog_manager.start(
        states.Main.MAIN,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    # Example of handling UnknownIntent Error and starting new dialog.
    logger.error("Restarting dialog: %s", event.exception)
    if isinstance(event.event, MessageCallback):
        callback: MessageCallback = event.event
        await event.event.callback_answer(
            notification=(
                "Bot process was restarted due to maintenance.\n"
                "Redirecting to main menu."
            ),
        )
        if callback.message:
            try:  # noqa: SIM105
                await callback.delete_message()
            except MaxBotApiError:
                pass  # whatever
    elif isinstance(event.event, MessageCreated):
        message: MessageCreated = event.event
        await message.answer_text(
            text=(
                "Bot process was restarted due to maintenance.\n"
                "Redirecting to main menu."
            ),
        )
    await dialog_manager.start(
        states.Main.MAIN,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


dialog_router = Router()
dialog_router.include_routers(
    layouts_dialog,
    scroll_dialog,
    main_dialog,
    calendar_dialog,
    selects_dialog,
    counter_dialog,
    multiwidget_dialog,
    switch_dialog,
    link_preview_dialog,
    about_dialog,
)


def setup_dp() -> Dispatcher:
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = MemoryStorage(key_builder)

    dp = Dispatcher(storage=storage)
    dp.message.register(start, MagicFilter(F.text == "/start"))
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )

    dp.include_routers(dialog_router)
    setup_dialogs(dp)

    return dp


async def main() -> None:
    # real main
    bot = Bot(token=os.environ["TOKEN"])
    dp = setup_dp()
    await LongPolling(dp).start(bot, drop_pending_updates=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
