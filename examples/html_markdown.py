import logging
import os

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()


# Html_text / md_text - сырой разбор; format задаёт отображение (HTML или Markdown)
@dp.message_created()
async def text_decoration_handler(update: MessageCreated) -> None:
    html = update.message.body.html_text
    md = update.message.body.md_text
    await update.reply_text(text=html)
    await update.reply_text(text=html, format=TextFormat.HTML)
    await update.reply_text(text=md)
    await update.reply_text(text=md, format=TextFormat.MARKDOWN)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
