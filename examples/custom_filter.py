# Кастомный фильтр - проверяет точное совпадение текста

import logging
import os

from maxo import Bot, Ctx, Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

dp = Dispatcher()


class MyFilter(BaseFilter[MessageCreated]):
    def __init__(self, my_text: str) -> None:
        self.my_text = my_text

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        if update.message.body.text is None:
            return False
        return update.message.body.text == self.my_text


@dp.message_created(MyFilter("привет"))
async def my_handler(message: MessageCreated) -> None:
    await message.answer_text("Ответ из кастомного фильтра!")


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(os.environ["TOKEN"])
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
