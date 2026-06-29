import logging
import os

from maxo import Bot, Ctx, Dispatcher
from maxo.enums import AttachmentType
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()


class AttachmentFilter(BaseFilter[MessageCreated]):
    def __init__(self, attachment_type: AttachmentType) -> None:
        self._attachment_type = attachment_type

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        for attachment in update.message.body.attachments or []:
            if attachment.type == self._attachment_type:
                return True

        # ruff: noqa: SIM103
        if self._attachment_type == AttachmentType.TEXT and update.message.body.text:
            return True

        return False


@dp.message_created(AttachmentFilter(AttachmentType.AUDIO))
async def audio_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил голосовое сообщение")
    await update.send_message(
        media=[update.message.body.audio.to_request()],
    )


@dp.message_created(AttachmentFilter(AttachmentType.CONTACT))
async def contact_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с контактом")
    await update.bot.send_message(
        chat_id=update.chat_id,
        attachments=[update.message.body.contact],
    )


@dp.message_created(AttachmentFilter(AttachmentType.FILE))
async def file_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с файлом")
    await update.send_message(
        media=[update.message.body.file.to_request()],
    )


@dp.message_created(AttachmentFilter(AttachmentType.IMAGE))
async def image_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с изображениями")
    await update.send_message(
        media=[photo.to_request() for photo in update.message.body.photo],
    )


@dp.message_created(AttachmentFilter(AttachmentType.LOCATION))
async def location_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с геопозицией")
    await update.bot.send_message(
        chat_id=update.chat_id,
        attachments=[update.message.body.location],
    )


@dp.message_created(AttachmentFilter(AttachmentType.SHARE))
async def share_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с предпросмотром ссылки")
    await update.bot.send_message(
        chat_id=update.chat_id,
        attachments=[update.message.body.share],
    )


@dp.message_created(AttachmentFilter(AttachmentType.STICKER))
async def sticker_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение со стикером")
    await update.bot.send_message(
        chat_id=update.chat_id,
        attachments=[update.message.body.sticker],
    )


@dp.message_created(AttachmentFilter(AttachmentType.VIDEO))
async def video_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил сообщение с видео")
    await update.send_message(
        media=[video.to_request() for video in update.message.body.video],
    )


@dp.message_created(AttachmentFilter(AttachmentType.TEXT))
async def text_handler(update: MessageCreated) -> None:
    await update.answer_text("Получил простое текстовое сообщение")


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
