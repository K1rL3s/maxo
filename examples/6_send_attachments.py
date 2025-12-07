import logging
import os

from maxo import Bot, Dispatcher
from maxo.routing.updates import MessageCreated
from maxo.utils.facades import MessageCreatedFacade
from maxo.utils.long_polling import LongPolling
from maxo.utils.upload_media import FSInputFile

dispatcher = Dispatcher()


@dispatcher.message_created()
async def attachments_handler(
    update: MessageCreated,
    facade: MessageCreatedFacade,
) -> None:
    # maxo.errors.api.MaxBotBadRequestError:
    # ('proto.payload', 'Must be only one file attachment in message')
    for file in (
        FSInputFile.image(path="./files/watermelon.jpg"),
        FSInputFile.file(path="files/watermelon.txt"),
        FSInputFile.audio(path="./files/watermelon.mp3"),
        FSInputFile.video(path="./files/watermelon.mp4"),
    ):
        await facade.send_message(media=(file,))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.environ["TOKEN"])
    LongPolling(dispatcher).run(bot)


if __name__ == "__main__":
    main()
