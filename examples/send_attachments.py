import logging
import os

from maxo import Bot, Dispatcher
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling
from maxo.types import UpdateContext
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
        requests = [attachment.to_request() for attachment in sent_attachments]
        await message.bot.send_message(
            user_id=update_context.user_id,
            chat_id=update_context.chat_id,
            attachments=requests,
        )

        # Отправка через Attachmets
        await message.bot.send_message(
            user_id=update_context.user_id,
            chat_id=update_context.chat_id,
            attachments=bot_message.body.attachments,
        )


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(token=os.environ["TOKEN"])
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
