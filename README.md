<p align="center">
  <a href="https://github.com/K1rL3s/maxo">
    <img width="200px" height="200px" alt="maxo - асинхронный Python-фреймворк для ботов мессенджера MAX (max.ru)" src="./docs/_static/maxo-logo.png">
  </a>
</p>
<h1 align="center">
  maxo - асинхронный Python-фреймворк для ботов MAX (max.ru)
</h1>

<div align="center">

[![License](https://img.shields.io/pypi/l/maxo.svg?style=flat)](https://github.com/K1rL3s/maxo/blob/master/LICENSE)
[![Status](https://img.shields.io/pypi/status/maxo.svg?style=flat)](https://pypi.org/project/maxo/)
[![PyPI](https://img.shields.io/pypi/v/maxo?label=pypi&style=flat)](https://pypi.org/project/maxo/)
[![Downloads](https://img.shields.io/pypi/dm/maxo?style=flat)](https://pypi.org/project/maxo/)
[![GitHub Repo stars](https://img.shields.io/github/stars/K1rL3s/maxo?style=flat)](https://github.com/K1rL3s/maxo/stargazers)
[![Supported python versions](https://img.shields.io/pypi/pyversions/maxo.svg?style=flat)](https://pypi.org/project/maxo/)
[![Docs](https://img.shields.io/readthedocs/maxo?style=flat)](https://maxo.readthedocs.io)
[![Tests](https://img.shields.io/github/actions/workflow/status/K1rL3s/maxo/test.yml?style=flat&label=tests)](https://github.com/K1rL3s/maxo/actions)
[![Coverage](https://codecov.io/gh/K1rL3s/maxo/graph/badge.svg?style=flat)](https://codecov.io/gh/K1rL3s/maxo)
[![DeepWiki](https://img.shields.io/badge/DeepWiki-K1rL3s%2Fmaxo-blue.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAyCAYAAAAnWDnqAAAAAXNSR0IArs4c6QAAA05JREFUaEPtmUtyEzEQhtWTQyQLHNak2AB7ZnyXZMEjXMGeK/AIi+QuHrMnbChYY7MIh8g01fJoopFb0uhhEqqcbWTp06/uv1saEDv4O3n3dV60RfP947Mm9/SQc0ICFQgzfc4CYZoTPAswgSJCCUJUnAAoRHOAUOcATwbmVLWdGoH//PB8mnKqScAhsD0kYP3j/Yt5LPQe2KvcXmGvRHcDnpxfL2zOYJ1mFwrryWTz0advv1Ut4CJgf5uhDuDj5eUcAUoahrdY/56ebRWeraTjMt/00Sh3UDtjgHtQNHwcRGOC98BJEAEymycmYcWwOprTgcB6VZ5JK5TAJ+fXGLBm3FDAmn6oPPjR4rKCAoJCal2eAiQp2x0vxTPB3ALO2CRkwmDy5WohzBDwSEFKRwPbknEggCPB/imwrycgxX2NzoMCHhPkDwqYMr9tRcP5qNrMZHkVnOjRMWwLCcr8ohBVb1OMjxLwGCvjTikrsBOiA6fNyCrm8V1rP93iVPpwaE+gO0SsWmPiXB+jikdf6SizrT5qKasx5j8ABbHpFTx+vFXp9EnYQmLx02h1QTTrl6eDqxLnGjporxl3NL3agEvXdT0WmEost648sQOYAeJS9Q7bfUVoMGnjo4AZdUMQku50McDcMWcBPvr0SzbTAFDfvJqwLzgxwATnCgnp4wDl6Aa+Ax283gghmj+vj7feE2KBBRMW3FzOpLOADl0Isb5587h/U4gGvkt5v60Z1VLG8BhYjbzRwyQZemwAd6cCR5/XFWLYZRIMpX39AR0tjaGGiGzLVyhse5C9RKC6ai42ppWPKiBagOvaYk8lO7DajerabOZP46Lby5wKjw1HCRx7p9sVMOWGzb/vA1hwiWc6jm3MvQDTogQkiqIhJV0nBQBTU+3okKCFDy9WwferkHjtxib7t3xIUQtHxnIwtx4mpg26/HfwVNVDb4oI9RHmx5WGelRVlrtiw43zboCLaxv46AZeB3IlTkwouebTr1y2NjSpHz68WNFjHvupy3q8TFn3Hos2IAk4Ju5dCo8B3wP7VPr/FGaKiG+T+v+TQqIrOqMTL1VdWV1DdmcbO8KXBz6esmYWYKPwDL5b5FA1a0hwapHiom0r/cKaoqr+27/XcrS5UwSMbQAAAABJRU5ErkJggg==)](https://deepwiki.com/K1rL3s/maxo)

</div>

<p align="center">
    <b>
        Асинхронный Python-фреймворк для разработки <a href="https://dev.max.ru/docs">ботов</a> в <a href="https://max.ru">MAX</a>
    </b>
</p>

<p align="center">
    <a href="https://maxo.readthedocs.io"><b>Документация</b></a><br><br>
    Интерфейс основан на <a href="https://github.com/aiogram/aiogram">aiogram</a><br>
    <a href="./src/maxo/dialogs">maxo/dialogs</a> сделано из <a href="https://github.com/Tishka17/aiogram_dialog">aiogram_dialog</a><br>
    <a href="./src/maxo/transport/webhook">maxo/transport/webhook</a> сделано из <a href="https://github.com/m-xim/aiogram-webhook">aiogram-webhook</a><br>
</p>

## Установка

Через `pip`:
```commandline
pip install maxo
```

В `pyproject.toml`:
```toml
[project]
dependencies = [
    "maxo",
]
```

## Особенности

- Асинхронность на базе `aiohttp` и [`unihttp`](https://github.com/goduni/unihttp) ([asyncio](https://docs.python.org/3/library/asyncio.html), [PEP 492](https://peps.python.org/pep-0492/))
- 100% покрытие типами, [`adaptix`](https://github.com/reagento/adaptix) для валидации данных
- Роутеры, фильтры, милдвари
- Встроенная машина состояний (FSM) и диалоги поверх них
- Поддержка лонг-поллинга и вебхуков через `aiohttp` и `fastapi`
- Интеграции с `dishka` и `magic_filter`
- Автогенерация методов, типов и апдейтов по [официальной документации](https://dev.max.ru/docs-api)

## Быстрый старт

Больше примеров в [примерах](./examples)

### Эхо-бот

```python
from maxo import Bot, Dispatcher
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling

bot = Bot("TOKEN")
dp = Dispatcher()

@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    text = message.text or "Текста нет"
    await message.answer(text)

LongPolling(dp).run(bot)
```

### Команды

```python
from maxo import Bot, Dispatcher
from maxo.routing.filters import Command, DeeplinkFilter
from maxo.routing.updates import BotStarted, MessageCreated
from maxo.transport.long_polling import LongPolling

bot = Bot("TOKEN")
dp = Dispatcher()

@dp.bot_started(DeeplinkFilter())
async def deeplink_handler(bot_started: BotStarted, deeplink: str) -> None:
    await bot_started.send_message(f"Привет! Я бот. Диплинк: {deeplink}")

@dp.bot_started()
async def start_handler(bot_started: BotStarted) -> None:
    await bot_started.send_message(f"Привет! Я бот. А ты {bot_started.user.fullname}")

@dp.message(Command("help"))
async def help_handler(message: MessageCreated) -> None:
    await message.send_message("За помощью обращайтесь в t.me/maxo_py")

LongPolling(dp).run(bot)
```

### Клавиатуры

```python
from magic_filter import F

from maxo import Bot, Dispatcher
from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters import CommandStart
from maxo.routing.updates import MessageCallback, MessageCreated
from maxo.transport.long_polling import LongPolling
from maxo.utils.builders import KeyboardBuilder

bot = Bot("TOKEN")
dp = Dispatcher()

@dp.message_created(CommandStart())
async def start_handler(message: MessageCreated) -> None:
    maxo_url = "https://github.com/K1rL3s/maxo"
    keyboard = (
        KeyboardBuilder()
        .add_callback(text="Колбэк", payload="click_me")
        .add_message(text="Сообщение")
        .add_link(text="Перейти в maxo", url=maxo_url)
        .add_clipboard(text="Скопировать maxo", payload=maxo_url)
        .add_request_contact(text="Поделиться контактами")
        .add_request_geo_location(text="Поделиться гео позицией")
        .adjust(2, 2, 1, 1)
    )
    await message.answer(text="Кнопочки :3", keyboard=keyboard.build())

@dp.message_callback(MagicFilter(F.payload == "callback_payload"))
async def button_handler(callback: MessageCallback) -> None:
    await callback.callback_answer("Вы нажали на кнопку!")

LongPolling(dp).run(bot)
```

### Вебхук

```python
import logging

from aiohttp import web

from maxo import Bot, Dispatcher, Router
from maxo.enums import TextFormat
from maxo.routing.updates import BotStarted, MessageCreated
from maxo.routing.utils import collect_used_updates
from maxo.transport.webhook.adapters.aiohttp import AiohttpWebAdapter
from maxo.transport.webhook.engines import SimpleEngine, WebhookEngine
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security, StaticSecretToken

bot = Bot("TOKEN")
router = Router()

@router.bot_started()
async def start_handler(bot_started: BotStarted) -> None:
    await bot_started.send_message(
        text=f"Привет из вебхука, {bot_started.user.first_name}!",
    )

@router.message_created()
async def echo_handler(message: MessageCreated) -> None:
    await message.answer(
        text=message.message.body.html_text,
        format=TextFormat.HTML,
    )

@router.after_startup()
async def on_startup(dispatcher: Dispatcher, webhook_engine: WebhookEngine) -> None:
    await webhook_engine.set_webhook(update_types=collect_used_updates(dispatcher))

def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.include(router)

    engine = SimpleEngine(
        dispatcher,
        bot,
        web_adapter=AiohttpWebAdapter(),
        routing=StaticRouting(url="https://example.com/webhook"),
        security=Security(secret_token=StaticSecretToken("pepa_pig")),
    )
    app = web.Application()
    engine.register(app)

    web.run_app(app, host="127.0.0.1", port=8080)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
```

## FAQ

### Что такое MAX?

[MAX](https://max.ru) - российский мессенджер. У него есть открытое [Bot API](https://dev.max.ru/docs-api), для работы с которым и создан `maxo`.

### Чем maxo отличается от aiogram?

`maxo` - отдельный фреймворк именно для ботов [MAX](https://max.ru), но интерфейс намеренно близок к [aiogram](https://github.com/aiogram/aiogram), чтобы переход был максимально безболезненным. Диалоги (`maxo.dialogs`) портированы из [aiogram_dialog](https://github.com/Tishka17/aiogram_dialog), вебхуки (`maxo.transport.webhook`) - из [aiogram-webhook](https://github.com/m-xim/aiogram-webhook).

### Поддерживает ли maxo вебхуки?

Да. Поддерживается и long-polling, и webhook через `aiohttp` или `fastapi` - см. примеры выше.

### Какой Python нужен?

Python 3.12, 3.13 или 3.14.

### Где взять токен бота MAX?

На [платформе для партнёров](https://business.max.ru/self).

### Как добавить FSM?

FSM встроена в `maxo` - есть `MemoryStorage` из коробки и опциональное хранилище в Redis (`maxo[redis]`). Подробности - в [документации](https://maxo.readthedocs.io).

## Связь
Если у вас есть вопросы, вы можете задать их в Телеграме [\@maxo_py](https://t.me/maxo_py) или [Максе](https://max.ru/join/rwJmWA4B5AipBiJdWRkORGjxFmqnJPUhJbQxxmscrnc)

