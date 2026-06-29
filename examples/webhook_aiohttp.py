import logging
import os

from aiohttp import web

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.routing.updates import MessageCreated
from maxo.routing.utils import collect_used_updates
from maxo.transport.webhook.adapters.aiohttp import AiohttpWebAdapter
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


def main() -> None:
    engine = SimpleEngine(
        dp,
        bot,
        web_adapter=AiohttpWebAdapter(),
        # Укажите путь, по которому к вам будут приходить апдейты из Макса
        routing=StaticRouting(url="https://example.com/webhook"),
        # security можно оставить None, если не используете секретный токен
        security=Security(secret_token=StaticSecretToken("pepapig")),
    )
    app = web.Application()
    engine.register(app)
    web.run_app(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
