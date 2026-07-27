"""
Dishka + custom middleware: middleware reads ctx[CONTAINER_NAME], gets a service,
puts result in ctx; handler uses ctx. Run: pip install maxo[dishka], then
python examples/dishka_middleware.py
"""

import asyncio
import logging
import os
from typing import Any

from dishka import (
    AsyncContainer,
    BaseScope,
    Provider,
    Scope,
    make_async_container,
    provide,
)

from maxo import Bot, Ctx, Dispatcher
from maxo.integrations.dishka import CONTAINER_NAME, setup_dishka
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.types import MessageCreated


class GreeterService:
    def greet(self, name: str) -> str:
        return f"Привет, {name}!"


class AppProvider(Provider):
    scope: BaseScope | None = Scope.APP

    @provide
    def bot(self) -> Bot:
        return Bot(os.environ["TOKEN"])

    @provide
    def dispatcher(self) -> Dispatcher:
        return Dispatcher()

    @provide
    def greeter(self) -> GreeterService:
        return GreeterService()


# После setup_dishka в ctx под ключом CONTAINER_NAME лежит request-scoped контейнер
class GreetingMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        container: AsyncContainer = ctx[CONTAINER_NAME]
        greeter = await container.get(GreeterService)
        name = "гость"
        ctx["greeting"] = greeter.greet(name)
        return await next(ctx)


# Greeting заполнен в middleware, хендлер получает его аргументом из ctx
async def message_handler(message: MessageCreated, greeting: str) -> None:
    await message.answer_text(greeting)


async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    container: AsyncContainer = make_async_container(AppProvider())
    bot = await container.get(Bot)
    dp = await container.get(Dispatcher)
    setup_dishka(container, dp, auto_inject=True)
    dp.message_created.middleware.outer(GreetingMiddleware())
    dp.message_created.handler(message_handler)
    try:
        await dp.start_polling(bot)
    finally:
        await container.close()  # Обязательно закрыть контейнер при выходе


if __name__ == "__main__":
    asyncio.run(main())
