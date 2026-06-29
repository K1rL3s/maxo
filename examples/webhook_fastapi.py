import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.routing.updates import MessageCreated
from maxo.routing.utils import collect_used_updates
from maxo.transport.webhook.adapters.fastapi import FastApiWebAdapter
from maxo.transport.webhook.engines import SimpleEngine, WebhookEngine
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security, StaticSecretToken

dp = Dispatcher()
bot = Bot(os.environ["TOKEN"])


@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    await message.answer_text(
        text=message.message.body.html_text,
        format=TextFormat.HTML,
    )


@dp.after_startup()
async def on_startup(dispatcher: Dispatcher, webhook_engine: WebhookEngine) -> None:
    await webhook_engine.set_webhook(update_types=collect_used_updates(dispatcher))


def main() -> FastAPI:
    engine = SimpleEngine(
        dp,
        bot,
        web_adapter=FastApiWebAdapter(),
        # Укажите путь, по которому к вам будут приходить апдейты из Макса
        routing=StaticRouting(url="https://example.com/webhook"),
        # security можно оставить None, если не используете секретный токен
        security=Security(secret_token=StaticSecretToken("pepapig")),
    )

    # В реализации FastApiWebAdapter в register игнорируются переданные
    # on_startup и on_shutdown. Разработчик должен сам определить lifespan,
    # в котором вызовет engine.on_startup и engine.on_shutdown для корректной работы
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        engine.register(app)
        await engine.on_startup(app)
        yield
        await engine.on_shutdown(app)

    return FastAPI(lifespan=lifespan)


logging.basicConfig(level=logging.DEBUG)
app = main()

# TOKEN=f9LHod fastapi dev ./examples/webhook_fastapi.py
