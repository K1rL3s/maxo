# Пример обработки всех типов апдейтов: сообщения, колбэки, события чата/бота

import logging
import os

from maxo import Bot, Dispatcher
from maxo.routing.updates import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    ChatTitleChanged,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
    UserRemovedFromChat,
)
from maxo.transport.long_polling import LongPolling

logger = logging.getLogger(__name__)

bot = Bot(token=os.environ["TOKEN"])
dp = Dispatcher()


@dp.message_created()
async def message_created_handler(message_created: MessageCreated) -> None:
    await message_created.reply_text(
        f"Привет! Я получил твое сообщение: '{message_created.message.body.text}'",
    )


@dp.message_edited()
async def message_edited_handler(message_edited: MessageEdited) -> None:
    await message_edited.send_message(
        "Я заметил, что ты отредактировал сообщение "
        f"(ID: {message_edited.message.body.mid})\n"
        f"Новый текст: '{message_edited.message.body.text}'",
    )


@dp.message_callback()
async def message_callback_handler(message_callback: MessageCallback) -> None:
    await message_callback.callback_answer(notification="Ты нажал кнопку!")
    await message_callback.answer_text(
        f"Данные колбэка "
        f"(ID: {message_callback.callback.callback_id}, "
        f"сообщение ID: {message_callback.unsafe_message.body.mid}): "
        f"{message_callback.callback.payload}",
    )


@dp.message_removed()
async def message_removed_handler(message_removed: MessageRemoved) -> None:
    await message_removed.send_message(
        f"Сообщение (ID: {message_removed.message_id}) "
        f"было удалено из чата (ID: {message_removed.chat_id})",
    )


@dp.bot_started()
async def bot_started_handler(bot_started: BotStarted) -> None:
    bot_info = await bot_started.get_my_info()
    await bot_started.send_message(
        f"Привет! Я {bot_info.first_name}. Спасибо, что запустил меня!",
    )


@dp.bot_stopped()
async def bot_stopped_handler(bot_stopped: BotStopped) -> None:
    logger.info(
        "Пользователь (ID: %s) остановил бота в чате (ID: %s)",
        bot_stopped.user.user_id,
        bot_stopped.chat_id,
    )


@dp.bot_added_to_chat()
async def bot_added_to_chat_handler(bot_added: BotAddedToChat) -> None:
    await bot_added.send_message(
        f"Всем привет! Я новый бот в чате (ID: {bot_added.chat_id}), "
        f"меня добавил пользователь (ID: {bot_added.user.user_id})",
    )
    members = await bot_added.get_members()
    await bot_added.send_message(f"Я вижу здесь {len(members.members)} участников")


@dp.bot_removed_from_chat()
async def bot_removed_from_chat_handler(bot_removed: BotRemovedFromChat) -> None:
    logger.info(
        "Бот был удален из чата (ID: %s) пользователем (ID: %s)",
        bot_removed.chat_id,
        bot_removed.user.user_id,
    )


@dp.user_added_to_chat()
async def user_added_to_chat_handler(user_added: UserAddedToChat) -> None:
    await user_added.send_message(
        f"Добро пожаловать в чат, {user_added.user.first_name} "
        f"(ID: {user_added.user.user_id})! "
        f"Я успешно обработал добавление нового пользователя",
    )


@dp.user_removed_from_chat()
async def user_removed_from_chat_handler(user_removed: UserRemovedFromChat) -> None:
    await user_removed.send_message(
        f"Пользователь {user_removed.user.first_name} "
        f"(ID: {user_removed.user.user_id}) покинул чат (ID: {user_removed.chat_id})",
    )


@dp.chat_title_changed()
async def chat_title_changed_handler(chat_title_changed: ChatTitleChanged) -> None:
    await chat_title_changed.send_message(
        f"Название чата (ID: {chat_title_changed.chat_id}) "
        f"было изменено на '{chat_title_changed.title}' "
        f"пользователем (ID: {chat_title_changed.user.user_id})",
    )


@dp.dialog_cleared()
async def dialog_cleared_handler(dialog_cleared: DialogCleared) -> None:
    await dialog_cleared.send_message(
        f"Диалог с пользователем (ID: {dialog_cleared.user.user_id}) в чате "
        f"(ID: {dialog_cleared.chat_id}) был очищен",
    )


@dp.dialog_muted()
async def dialog_muted_handler(dialog_muted: DialogMuted) -> None:
    await dialog_muted.send_message(
        f"Диалог с пользователем (ID: {dialog_muted.user.user_id}) в чате "
        f"(ID: {dialog_muted.chat_id}) заглушен до {dialog_muted.muted_until}",
    )


@dp.dialog_removed()
async def dialog_removed_handler(dialog_removed: DialogRemoved) -> None:
    logger.info(
        "Диалог с пользователем (ID: %s) был удален из чата (ID: %s)",
        dialog_removed.user.user_id,
        dialog_removed.chat_id,
    )


@dp.dialog_unmuted()
async def dialog_unmuted_handler(dialog_unmuted: DialogUnmuted) -> None:
    await dialog_unmuted.send_message(
        f"Диалог с пользователем (ID: {dialog_unmuted.user.user_id}) в чате "
        f"(ID: {dialog_unmuted.chat_id}) был разглушен",
    )


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
