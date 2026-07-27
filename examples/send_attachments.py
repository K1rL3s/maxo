import logging
import os
from typing import cast

from maxo import Bot, Dispatcher
from maxo.omit import Omitted
from maxo.types import MessageCreated, UpdateContext
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.utils.upload_media import FSInputFile

dp = Dispatcher()


@dp.message_created()
async def attachments_handler(
    message: MessageCreated,
    update_context: UpdateContext,
) -> None:
    # В одном сообщении API принимает только один файл - отправляем по одному.
    # При нескольких вложениях: maxo.errors.api.MaxBotBadRequestError
    # ('proto.payload', 'Must be only one file attachment in message')
    for file in (
        FSInputFile.image(path="./files/watermelon.jpg"),
        FSInputFile.file(path="files/watermelon.txt"),
        FSInputFile.audio(path="./files/watermelon.mp3"),
        FSInputFile.video(path="./files/watermelon.mp4"),
    ):
        # Отправка через InputFile
        bot_message = await message.send_message(media=(file,))

        sent_attachments = bot_message.body.attachments or []

        # Отправка через AttachmetsRequests
        requests: list[AttachmentsRequests | Attachments] = [
            attachment.to_request() for attachment in sent_attachments
        ]
        await message.bot.send_message(
            user_id=update_context.user_id or Omitted(),
            chat_id=update_context.chat_id or Omitted(),
            attachments=requests,
        )

        # Отправка через Attachmets
        await message.bot.send_message(
            user_id=update_context.user_id or Omitted(),
            chat_id=update_context.chat_id or Omitted(),
            attachments=cast(
                "list[AttachmentsRequests | Attachments] | None",
                bot_message.body.attachments,
            ),
        )


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(token=os.environ["TOKEN"])
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
