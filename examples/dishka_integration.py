"""
Dishka integration example: container, setup_dishka, handler with auto_inject.
Run: pip install maxo[dishka], then python examples/dishka_integration.py
"""

import asyncio
import logging
import os

from dishka import (
    AsyncContainer,
    FromDishka,
    Provider,
    Scope,
    make_async_container,
    provide,
)

from maxo import Bot, Dispatcher
from maxo.integrations.dishka import setup_dishka
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling


class GreeterService:
    def greet(self, name: str) -> str:
        return f"Привет, {name}!"


class AppProvider(Provider):
    scope = Scope.APP

    @provide
    def bot(self) -> Bot:
        return Bot(os.environ["TOKEN"])

    @provide
    def dispatcher(self) -> Dispatcher:
        return Dispatcher()

    @provide
    def greeter(self) -> GreeterService:
        return GreeterService()


# greeter приходит из контейнера по типу аргумента (auto_inject)
async def start_handler(
    message: MessageCreated,
    greeter: FromDishka[GreeterService],
) -> None:
    text = greeter.greet("друг")
    await message.answer_text(text)


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    container: AsyncContainer = make_async_container(AppProvider())
    bot = await container.get(Bot)
    dp = await container.get(Dispatcher)
    # auto_inject=True - зависимости подставляются в хендлеры по типам аргументов
    setup_dishka(container, dp, auto_inject=True)
    dp.message_created.handler(start_handler, CommandStart())
    try:
        await LongPolling(dp).start(bot)
    finally:
        await container.close()  # Обязательно закрыть контейнер при выходе


if __name__ == "__main__":
    asyncio.run(main())
