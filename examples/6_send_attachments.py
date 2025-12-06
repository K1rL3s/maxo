import asyncio
import os

from maxo.bot import MaxoBot
from maxo.dispatcher import Dispatcher
from maxo.types import MessageCreated
from maxo.utils.facades import MessageCreatedFacade
from maxo.utils.upload_media import FSInputFile

# Initialize bot and dispatcher
bot = MaxoBot(token=os.getenv("BOT_TOKEN"))
dispatcher = Dispatcher(bot)


@dispatcher.message_created()
async def attachments_handler(
    update: MessageCreated,
    facade: MessageCreatedFacade,
) -> None:
    # Example of sending multiple attachments
    # Ensure these files exist in examples/files/ directory
    await facade.send_message(
        media=[
            FSInputFile.image(path="examples/files/image.png"),
            FSInputFile.video(path="examples/files/video.mp4"),
            FSInputFile.audio(path="examples/files/audio.mp3"),
            FSInputFile.file(path="examples/files/document.txt"),
        ]
    )


async def main():
    await dispatcher.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
