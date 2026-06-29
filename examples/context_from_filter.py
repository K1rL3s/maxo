import logging
import os
from typing import Any

from maxo import Bot, Ctx, Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling
from maxo.types.user import User

dp = Dispatcher()


# Фильтр при совпадении записывает в ctx - хендлер получает name из ctx
class HelloFilter(BaseFilter[MessageCreated]):
    def __init__(self, name: str | None = None) -> None:
        self.name = name

    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
    ) -> bool:
        text = update.message.body.text
        if text is not None and text.casefold() == "привет":
            user: User = ctx["event_from_user"]
            ctx["name"] = user.fullname
            return True

        return False


@dp.message_created(HelloFilter())
async def my_handler(message: MessageCreated, name: str) -> Any:
    return await message.answer_text(f"Привет, {name}!")


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(os.environ["TOKEN"])
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
