import logging
import os

from aiohttp import web

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.transport.webhook.engines.single import SingleBotEngine
from maxo.transport.webhook.route import Route
from maxo.transport.webhook.security import Security, StaticSecret
from maxo.transport.webhook.web.aiohttp import AiohttpAdapter
from maxo.types import MessageCreated

dp = Dispatcher()
bot = Bot(os.environ["TOKEN"])


@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    await message.answer_text(
        text=message.message.body.html_text,
        format=TextFormat.HTML,
    )


def main() -> None:
    engine = SingleBotEngine(
        dp,
        bot,
        web=AiohttpAdapter(),
        # Укажите путь, по которому к вам будут приходить апдейты из Макса
        route=Route(base_url="https://example.com", path="/telegram/webhook"),
        # security можно оставить None, если не используете секретный токен
        security=Security(secret=StaticSecret("webhook-secret")),
    )

    app = web.Application()
    engine.register(app)

    async def subscribe(_app: web.Application) -> None:
        await engine.subscribe()

    app.on_startup.append(subscribe)
    web.run_app(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
