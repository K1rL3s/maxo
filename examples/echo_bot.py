import logging
import os

from maxo import Bot, Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.utils import inline_ctx
from maxo.transport.long_polling import LongPolling
from maxo.types import MessageCreated

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()



class MyFilter(BaseFilter[MessageCreated]):
    @inline_ctx
    async def __call__(self) -> bool:
        return True


# Без фильтра - хендлер получает любое сообщение
@dp.message_created(MyFilter())
async def echo_handler(update: MessageCreated) -> None:
    text = update.message.body.text or "Текста нет"
    await update.answer(text=text)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
