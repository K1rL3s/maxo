import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.transport.webhook.engines.single import SingleBotEngine
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.security import Security, StaticSecret
from maxo.transport.webhook.web.fastapi import FastAPIAdapter
from maxo.types import MessageCreated

dp = Dispatcher()
bot = Bot(os.environ["TOKEN"])


@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    await message.answer_text(
        text=message.message.body.html_text,
        format=TextFormat.HTML,
    )


def main() -> FastAPI:
    engine = SingleBotEngine(
        dp,
        bot,
        web=FastAPIAdapter(),
        # Укажите путь, по которому к вам будут приходить апдейты из Макса
        route=Route(base_url="https://example.com", path="/webhook"),
        # security можно оставить None, если не используете секретный токен
        security=Security(secret=StaticSecret("webhook-secret")),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        await engine.subscribe()
        yield

    app = FastAPI(lifespan=lifespan)
    engine.register(app)

    return app


logging.basicConfig(level=logging.DEBUG)
app = main()

# TOKEN=f9LHod fastapi dev ./examples/webhook_fastapi.py
