<p align="center">
  <a href="https://github.com/K1rL3s/maxo">
    <img width="200px" height="200px" alt="maxo - библиотека и асинхронный Python-фреймворк для разработки ботов MAX (max.ru) и работы с MAX Bot API" src="https://raw.githubusercontent.com/K1rL3s/maxo/refs/heads/master/docs/_static/maxo-logo.png">
  </a>
</p>
<h1 align="center">
  maxo - библиотека и асинхронный Python-фреймворк для разработки ботов MAX (max.ru) и работы с MAX Bot API
</h1>

<div align="center">

[![License](https://img.shields.io/pypi/l/maxo.svg?style=flat)](https://github.com/K1rL3s/maxo/blob/master/LICENSE)
[![Status](https://img.shields.io/pypi/status/maxo.svg?style=flat)](https://pypi.org/project/maxo/)
[![PyPI](https://img.shields.io/pypi/v/maxo?label=pypi&style=flat)](https://pypi.org/project/maxo/)
[![Downloads](https://img.shields.io/pypi/dm/maxo?style=flat)](https://pypi.org/project/maxo/)
[![GitHub Repo Stars](https://img.shields.io/github/stars/K1rL3s/maxo?style=flat)](https://github.com/K1rL3s/maxo/stargazers)
[![GitHub Repo Forks](https://img.shields.io/github/forks/K1rL3s/maxo?style=flat)](https://github.com/K1rL3s/maxo/forks)
[![Supported python versions](https://img.shields.io/pypi/pyversions/maxo.svg?style=flat)](https://pypi.org/project/maxo/)
[![Docs](https://img.shields.io/readthedocs/maxo?style=flat)](https://maxo.readthedocs.io)
[![Tests](https://img.shields.io/github/actions/workflow/status/K1rL3s/maxo/test.yml?style=flat&label=tests)](https://github.com/K1rL3s/maxo/actions)
[![Lint](https://img.shields.io/github/actions/workflow/status/K1rL3s/maxo/lint.yml?style=flat&label=lint)](https://github.com/K1rL3s/maxo/actions)
[![Coverage](https://codecov.io/gh/K1rL3s/maxo/graph/badge.svg?style=flat)](https://codecov.io/gh/K1rL3s/maxo)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/K1rL3s/maxo)
[![Context7](https://img.shields.io/badge/Context7-Ask_AI-007a55)](https://context7.com/K1rL3s/maxo)

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

## Почему maxo?

- Интерфейс намеренно близок к `aiogram`: роутеры, фильтры, мидлвари, FSM и диалоги работают так, как вы привыкли
- Диалоги (`maxo.dialogs`): окна, виджеты, пагинация, календарь. Интерфейс можно посмотреть в браузере до запуска бота, а сценарии - тестировать без сети
- Long-polling и вебхуки (`aiohttp` / `fastapi`), FSM с Redis, DI через `dishka` и фильтры на `magic_filter`
- Методы, типы и апдейты генерируются по [официальной документации MAX Bot API](https://dev.max.ru/docs-api) - меньше расхождений с платформой
- 100% аннотаций и `mypy --strict` - ошибки видно в IDE, а не в проде
- Ошибки API типизированы: можно писать `except MaxBotTooManyRequestsError`, а не разбирать голый HTTP-ответ
- Российский доверенный сертификат уже вшит в HTTP-клиент, настраивать SSL для API MAX вручную не нужно
- Асинхронность на `aiohttp` и [`unihttp`](https://github.com/goduni/unihttp), валидация данных через [`adaptix`](https://github.com/reagento/adaptix), [документация](https://maxo.readthedocs.io) на русском

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

## Для чего подходит maxo

- Разработка ботов MAX на Python
- Работа с MAX Bot API
- long-polling и webhook для MAX
- FSM, диалоги и inline-клавиатуры для ботов
- Миграция с aiogram-подхода на MAX

## Быстрый старт

Больше примеров в [примерах](./examples)

### Эхо-бот

```python
from maxo import Bot, Dispatcher
from maxo.types import MessageCreated

bot = Bot("TOKEN")
dp = Dispatcher()

@dp.message_created()
async def echo_handler(message: MessageCreated) -> None:
    text = message.text or "Текста нет"
    await message.answer(text)

dp.run_polling(bot)
```

### Команды

```python
from maxo import Bot, Dispatcher
from maxo.routing.filters import Command, DeeplinkFilter
from maxo.types import BotStarted, MessageCreated

bot = Bot("TOKEN")
dp = Dispatcher()

@dp.bot_started(DeeplinkFilter())
async def deeplink_handler(bot_started: BotStarted, deeplink: str) -> None:
    await bot_started.send_message(f"Привет! Я бот. Диплинк: {deeplink}")

@dp.bot_started()
async def start_handler(bot_started: BotStarted) -> None:
    await bot_started.send_message(f"Привет! Я бот. А ты {bot_started.user.fullname}")

@dp.message_created(Command("help"))
async def help_handler(message: MessageCreated) -> None:
    await message.send_message("За помощью обращайтесь в t.me/maxo_py")

dp.run_polling(bot)
```

### Клавиатуры

```python
from magic_filter import F

from maxo import Bot, Dispatcher
from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters import CommandStart
from maxo.types import MessageCallback, MessageCreated
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
        .add_request_geo_location(text="Поделиться геопозицией")
        .adjust(2, 2, 1, 1)
    )
    await message.answer(text="Кнопочки :3", keyboard=keyboard.build())

@dp.message_callback(MagicFilter(F.payload == "click_me"))
async def button_handler(callback: MessageCallback) -> None:
    await callback.callback_answer("Вы нажали на кнопку!")

dp.run_polling(bot)
```

### Диалоги

Многошаговый сценарий - это окна и виджеты, переходами управляет менеджер
диалога. Окна можно отрисовать в HTML-превью без запуска бота, а сценарии -
тестировать без сети через `maxo.dialogs.test_tools`:

```python
from maxo import Bot, Dispatcher
from maxo.dialogs import Dialog, DialogManager, StartMode, Window, setup_dialogs
from maxo.dialogs.widgets.kbd import Button
from maxo.dialogs.widgets.text import Const
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.routing.filters import CommandStart
from maxo.types import MessageCallback, MessageCreated

bot = Bot("TOKEN")
# Для диалогов нужен key builder с destiny
dp = Dispatcher(key_builder=DefaultKeyBuilder(with_destiny=True))

class MainState(StatesGroup):
    main = State()

async def close_dialog(
    callback: MessageCallback,
    button: Button,
    manager: DialogManager,
) -> None:
    await manager.done()

dialog = Dialog(
    Window(
        Const("Главное меню"),
        Button(Const("Закрыть"), id="close", on_click=close_dialog),
        state=MainState.main,
    ),
)

@dp.message_created(CommandStart())
async def start_handler(
    message: MessageCreated,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(MainState.main, mode=StartMode.RESET_STACK)

dp.include(dialog)
setup_dialogs(dp)

dp.run_polling(bot)
```

### Вебхук

```python
import logging

from aiohttp import web

from maxo import Bot, Dispatcher, Router
from maxo.enums import TextFormat
from maxo.routing.utils import collect_used_updates
from maxo.transport.webhook import (
    Route,
    SingleBotEngine,
    WebhookConfig,
)
from maxo.transport.webhook.security import Security, StaticSecret
from maxo.transport.webhook.web.aiohttp import AiohttpAdapter
from maxo.types import BotStarted, MessageCreated

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

def main() -> None:
    dispatcher = Dispatcher()
    dispatcher.include(router)

    engine = SingleBotEngine(
        dispatcher,
        bot,
        web=AiohttpAdapter(),
        route=Route(base_url="https://example.com", path="/webhook"),
        security=Security(secret=StaticSecret("pepa_pig")),
    )
    app = web.Application()
    engine.register(app)

    async def subscribe(_app: web.Application) -> None:
        await engine.subscribe(
            WebhookConfig(update_types=list(collect_used_updates(dispatcher))),
        )

    app.on_startup.append(subscribe)
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

### Можно ли перенести бота с aiogram на maxo?

Код один в один не переносится: MAX и Telegram - разные платформы со своими типами и методами. Но подход остаётся тем же: роутеры, фильтры, хэндлеры, FSM и диалоги называются и ведут себя привычно, поэтому переучиваться почти не придётся.

### Поддерживает ли maxo вебхуки?

Да. Поддерживается и long-polling, и webhook через `aiohttp` или `fastapi` - см. примеры выше.

### Какой Python нужен?

Python 3.12, 3.13 или 3.14.

### Где взять токен бота MAX?

На [платформе для партнёров](https://business.max.ru/self).

### Как добавить FSM?

FSM встроена в `maxo` - есть `MemoryStorage` из коробки и опциональное хранилище в Redis (`maxo[redis]`). Подробности - в [документации](https://maxo.readthedocs.io).

### Можно ли отправлять фото, видео и файлы?

Да. `maxo` умеет отправлять и принимать вложения - фото, видео, аудио и документы - через `InputFile` (загрузка файла) или по токену уже загруженного медиа. Крупные файлы грузятся частями (resumable). Подробности - в [документации](https://maxo.readthedocs.io).

### Есть ли dependency injection?

Да, через интеграцию с [`dishka`](https://github.com/reagento/dishka) (`maxo[dishka]`). Зависимости можно прокидывать в хэндлеры, фильтры и мидлвари.

### Можно ли обслуживать несколько ботов в одном приложении?

Да. `SingleBotEngine` обслуживает одного бота, а для нескольких есть `TokenEngine`: он достаёт токен из параметра маршрута и сам заводит бота под него. Маршрут описывается как `Route(path="/webhook/{bot_token}", params={"bot_token": BotTokenParam()})`, боты добавляются и убираются на лету через `add_bot(token)` / `remove_bot(bot_id)`; есть и `BotIdParam`, если в URL приходит id. Своя стратегия выбора бота - наследник `BaseMultiBotEngine` с методом `_resolve_bot(route_params)`.

### Как масштабировать бота под нагрузку?

Для продакшена используйте вебхуки: сервер MAX доставляет каждый апдейт один раз, и нагрузку можно распределить между воркерами (например, за Nginx или в Kubernetes). Long-polling для этого не подходит - при нескольких процессах с одним токеном апдейты дублируются.

### Как тестировать бота без реального MAX?

Для диалогов есть `maxo.dialogs.test_tools`: `BotClient` эмулирует пользователя, `MockMessageManager` записывает отправленные сообщения, локаторы находят кнопки по тексту. Сценарий "клик по кнопке - смена окна - новый текст" проверяется без единого сетевого вызова. Пример - в [examples/dialogs_testing.py](./examples/dialogs_testing.py).

### maxo бесплатный? Какая лицензия?

Да, `maxo` - open-source под лицензией Apache 2.0. Можно использовать в том числе в коммерческих проектах.


## Связь
Если у вас есть вопросы, вы можете задать их в Телеграме [\@maxo_py](https://t.me/maxo_py) или [Максе](https://max.ru/join/rwJmWA4B5AipBiJdWRkORGjxFmqnJPUhJbQxxmscrnc)
