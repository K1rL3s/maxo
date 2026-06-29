import logging
import os
from typing import Any

from maxo import Bot, Ctx, Dispatcher
from maxo.routing.filters.base import BaseFilter
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling


# Outer выполняется всегда и до фильтров; inner - после всех фильтров, если они прошли
class OuterMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        print("Исполнится перед фильтрами")
        result = await next(ctx)
        print("Исполнится после фильтров")
        return result


class InnerMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        print("Исполнится перед хендлером")
        result = await next(ctx)
        print("Исполнится после хендлера")
        return result


class ContainsTextFilter(BaseFilter[MessageCreated]):
    def __init__(self, text: str) -> None:
        self._text = text

    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
    ) -> bool:
        if update.message.body.text is None:
            return False

        return self._text in update.message.body.text


dp = Dispatcher()
dp.message_created.middleware.inner(InnerMiddleware())
dp.message_created.middleware.outer(OuterMiddleware())


# Фильтры можно комбинировать: & (и), | (или)
@dp.message_created(
    (ContainsTextFilter("gojo") & ContainsTextFilter("maki"))
    | ContainsTextFilter("sukuna"),
)
async def echo_handler(_: MessageCreated) -> None:
    print("Исполнение хендлера")


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(os.environ["TOKEN"])
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
