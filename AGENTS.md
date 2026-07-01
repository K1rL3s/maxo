# AGENTS.md — Полное руководство по maxo для AI-агентов

> **maxo** — асинхронный фреймворк для разработки ботов на платформе max.ru (Python 3.12–3.14). Версия: 0.5.3.

Это руководство даёт AI-агенту **полное понимание** фреймворка: архитектуру, API, паттерны, тонкости и лучшие практики.

---

## 1. Быстрый старт

### Установка

```bash
pip install maxo
# Дополнительно:
pip install maxo[dishka]     # DI через dishka
pip install maxo[redis]      # RedisStorage для FSM (production)
pip install maxo[magic_filter]  # MagicFilter для декларативных фильтров
pip install maxo[preview]    # HTML-превью диалогов + graphviz
```

### Минимальный эхо-бот

```python
import os
from maxo import Bot, Dispatcher
from maxo.routing.updates.message_created import MessageCreated
from maxo.utils.facades.updates.message_created import MessageCreatedFacade
from maxo.transport.long_polling import LongPolling

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()

@dp.message_created()
async def echo_handler(update: MessageCreated, facade: MessageCreatedFacade) -> None:
    text = update.message.body.text or "Текста нет"
    await facade.answer_text(text)

LongPolling(dp).run(bot)
```

### Основные импорты

```python
from maxo import Bot, Dispatcher, Router, Ctx
```

---

## 2. Архитектура обработки событий

### Поток обработки

```
Long Polling / Webhook
        ↓
    Dispatcher (корневой роутер)
        ↓
    Router.include(router) — порядок = приоритет
        ↓
    Outer Middleware → Фильтры → Inner Middleware → Handler
        ↓
    (первый совпавший обработчик — остальные пропускаются)
```

### Dispatcher vs Router

**Dispatcher** — корневой роутер. Инициализирует FSM, мидлвари, фасады.
```python
dp = Dispatcher(
    storage=MemoryStorage(),           # Хранилище FSM (по умолчанию MemoryStorage)
    events_isolation=None,             # Блокировка событий (для multi-instance)
    key_builder=None,                  # DefaultKeyBuilder(with_destiny=True) для dialogs!
    disable_fsm=False,                 # Отключить FSM
    workflow_data={"key": "value"},    # Глобальные данные для обработчиков
)
```

**Router** — модульный роутер для разделения логики:
```python
admin_router = Router(name="admin")
shop_router = Router(name="shop")

dp.include(admin_router, shop_router)  # Порядок = приоритет обработки
```

**Фильтр на весь роутер:**
```python
group_router.message_created.filter(IsGroupChat())
# Все обработчики group_router.message_created будут с этим фильтром
```

### Порядок `include()` критичен!

```python
dp.include(router1)  # Проверяется ПЕРВЫМ
dp.include(router2)  # Проверяется ВТОРЫМ
```
Первый совпавший обработчик **останавливает** распространение. Если `router1` обработал событие, `router2` не получит его.

### Сигналы жизненного цикла

Сигналы вызывают **ВСЕ** зарегистрированные обработчики (не первый совпавший):

```python
from maxo import Bot

@dp.before_startup()
async def on_before_start(bot: Bot) -> None:
    """До подключения бота. Бот ещё не подключён к API."""
    pass

@dp.after_startup()
async def on_after_start(bot: Bot, dispatcher: Dispatcher) -> None:
    """После подключения. Бот доступен для отправки сообщений."""
    info = await bot.get_my_info()
    print(f"Бот @{info.username} запущен!")
    # Можно передать данные в обработчики:
    dispatcher.workflow_data["admin_ids"] = [1, 2, 3]

@dp.before_shutdown()
async def on_before_stop(bot: Bot) -> None:
    """До отключения. Бот ещё активен."""
    pass

@dp.after_shutdown()
async def on_after_stop(bot: Bot) -> None:
    """После отключения. Бот отключён."""
    pass
```

---

## 3. Типы событий (Updates) — ВСЕ 17 типов

Все события наследуют от `MaxUpdate` (имеют `timestamp: datetime`).

### 3.1. MessageCreated — новое сообщение

**Декоратор:** `@router.message_created()`

```python
from maxo.routing.updates.message_created import MessageCreated

@dp.message_created()
async def handler(update: MessageCreated, facade: MessageCreatedFacade) -> None:
    pass
```

**Поля MessageCreated:**

| Поле | Тип | Описание |
|------|-----|----------|
| `message` | `Message` | Объект сообщения |
| `user_locale` | `Omittable[str \| None]` | Язык пользователя (только в диалогах) |
| `text` (property) | `str \| None` | Сокращение для `message.body.text` |

**Объект Message:**

| Поле | Тип | Описание |
|------|-----|----------|
| `body` | `MessageBody` | Содержимое: `text`, `mid`, `seq`, `html_text`, `keyboard`, `attachments` |
| `recipient` | `Recipient` | `chat_id`, `user_id`, `chat_type` |
| `sender` | `Omittable[User]` | Отправитель (может отсутствовать в каналах!) |
| `timestamp` | `datetime` | Время отправки |
| `link` | `Omittable[LinkedMessage \| None]` | Пересланное/ответное сообщение |
| `stat` | `Omittable[MessageStat \| None]` | Статистика (только каналы) |
| `url` | `Omittable[str \| None]` | Публичная ссылка (только каналы) |
| `generated_url` (property) | `str` | Генерирует ссылку на сообщение |

**MessageBody:**
- `text: Omittable[str \| None]` — текст
- `html_text: Omittable[str \| None]` — HTML-текст
- `attachments: Omittable[list[Attachment]]` — вложения
- `keyboard: Omittable[InlineKeyboard]` — клавиатура
- `mid`, `seq` — идентификаторы

### 3.2. MessageCallback — нажатие inline-кнопки

**Декоратор:** `@router.message_callback()`

```python
from maxo.routing.updates.message_callback import MessageCallback

@dp.message_callback()
async def handler(update: MessageCallback, facade: MessageCallbackFacade) -> None:
    pass
```

**Поля:**

| Поле | Тип | Описание |
|------|-----|----------|
| `callback` | `Callback` | Объект callback |
| `message` | `Message \| None` | Исходное сообщение (может быть `None` если удалено!) |
| `user_locale` | `Omittable[str \| None]` | Язык пользователя |
| `callback_id` (property) | `str` | ID callback |
| `payload` (property) | `str \| None` | Токен кнопки |
| `user` (property) | `User` | Пользователь, нажавший кнопку |

**Callback:**
- `callback_id: str`
- `payload: Omittable[str]`
- `timestamp: datetime`
- `user: User`

### 3.3. MessageEdited — редактирование сообщения

**Декоратор:** `@router.message_edited()`
- `message: Message` — отредактированное сообщение

### 3.4. MessageRemoved — удаление сообщения

**Декоратор:** `@router.message_removed()`
- `chat_id: int`
- `message_id: str`
- `user_id: int` — удаливший пользователь

### 3.5. BotStarted — запуск бота (deep link)

**Декоратор:** `@router.bot_started()`

| Поле | Тип | Описание |
|------|-----|----------|
| `chat_id` | `int` | |
| `user` | `User` | |
| `payload` | `Omittable[str \| None]` | Данные из deep link |
| `user_locale` | `Omittable[str]` | |

### 3.6. BotStopped — остановка бота

**Декоратор:** `@router.bot_stopped()`
- `chat_id: int`, `user: User`, `user_locale: Omittable[str]`

### 3.7. UserAddedToChat — пользователь добавлен в чат

**Декоратор:** `@router.user_added_to_chat()`
- `chat_id: int`, `user: User` (добавленный), `is_channel: bool`
- `inviter_id: Omittable[int \| None]` — кто добавил (`None` если по ссылке)

### 3.8. UserRemovedFromChat — пользователь удалён из чата

**Декоратор:** `@router.user_removed_from_chat()`
- `chat_id: int`, `user: User` (удалённый), `is_channel: bool`
- `admin_id: Omittable[int]` — админ (`None` если сам ушёл)

### 3.9. BotAddedToChat — бот добавлен в чат

**Декоратор:** `@router.bot_added_to_chat()`
- `chat_id: int`, `user: User` (добавивший), `is_channel: bool`

### 3.10. BotRemovedFromChat — бот удалён из чата

**Декоратор:** `@router.bot_removed_from_chat()`
- `chat_id: int`, `user: User` (удаливший), `is_channel: bool`

### 3.11. ChatTitleChanged — изменён заголовок чата

**Декоратор:** `@router.chat_title_changed()`
- `chat_id: int`, `title: str`, `user: User`

### 3.12. DialogCleared — диалог очищен

**Декоратор:** `@router.dialog_cleared()`
- `chat_id: int`, `user: User`, `user_locale: Omittable[str]`

### 3.13. DialogMuted — диалог замучен

**Декоратор:** `@router.dialog_muted()`
- `chat_id: int`, `muted_until: datetime`, `user: User`, `user_locale: Omittable[str]`

### 3.14. DialogUnmuted — диалог размучен

**Декоратор:** `@router.dialog_unmuted()`
- `chat_id: int`, `user: User`, `user_locale: Omittable[str]`

### 3.15. DialogRemoved — диалог удалён

**Декоратор:** `@router.dialog_removed()`
- `chat_id: int`, `user: User`, `user_locale: Omittable[str]`

### 3.16. ErrorEvent — ошибка

**Декоратор:** `@router.error()`

```python
from maxo.errors import ErrorEvent

@dp.error()
async def global_error(event: ErrorEvent, facade: ErrorEventFacade) -> None:
    print(f"Ошибка: {event.exception}")
    print(f"Исходное событие: {event.update}")
```

| Поле | Тип | Описание |
|------|-----|----------|
| `exception` | `Exception` | Исключение |
| `update` | `MaxoUpdate` | Исходное событие |

### 3.17. Enums — UpdateType

```python
from maxo.enums import UpdateType
# MESSAGE_CREATED, MESSAGE_CALLBACK, MESSAGE_EDITED, MESSAGE_REMOVED,
# BOT_STARTED, BOT_STOPPED, USER_ADDED_TO_CHAT, USER_REMOVED_FROM_CHAT,
# BOT_ADDED_TO_CHAT, BOT_REMOVED_FROM_CHAT, CHAT_TITLE_CHANGED,
# DIALOG_CLEARED, DIALOG_REMOVED, DIALOG_MUTED, DIALOG_UNMUTED
```

---

## 4. Bot — ВСЕ методы API

### Инициализация

```python
bot = Bot(
    token="YOUR_TOKEN",
    defaults=BotDefaults(...),          # Опционально: настройки по умолчанию
    warming_up=True,                    # Прогрев соединения
    middleware=[...],                   # HTTP-level middleware (unihttp.AsyncMiddleware)
    json_dumps=json.dumps,
    json_loads=json.loads,
)
```

### Управление

```python
await bot.start()           # Подключить бота
await bot.close()           # Отключить
async with bot.context():   # Async context manager (auto_close=True)
    ...
```

### Bots API

```python
info = await bot.get_my_info()  # -> BotInfo (username, first_name, ...)
await bot.edit_bot_info(
    first_name="Новое имя",
    last_name=None,
    description="Описание",
    commands=[BotCommand(command="start", description="Запуск")],
    photo=PhotoAttachmentRequestPayload(...),
)  # -> BotInfo
```

### Messages API

```python
# Отправка сообщения
result = await bot.send_message(
    chat_id=123,
    user_id=None,
    text="Привет!",
    attachments=None,
    link=None,
    notify=True,                              # Уведомление
    format=TextFormat.HTML,                   # HTML или MARKDOWN
    disable_link_preview=False,               # Отключить превью ссылок
)  # -> SendMessageResult

# Редактирование
await bot.edit_message(
    message_id="msg_123",
    text="Новый текст",
    attachments=None,
    link=None,
    notify=True,
    format=TextFormat.HTML,
)  # -> SimpleQueryResult

# Удаление
await bot.delete_message(message_id="msg_123")  # -> SimpleQueryResult

# Ответ на callback
await bot.answer_on_callback(
    callback_id="cb_123",
    message=NewMessageBody(text="Ответ"),       # Новое тело сообщения
    notification="Уведомление",                  # Текст уведомления
)  # -> SimpleQueryResult

# Получение сообщения
msg = await bot.get_message_by_id(message_id="msg_123")  # -> Message

# Список сообщений
msgs = await bot.get_messages(
    chat_id=123,
    count=50,
    from_=datetime(2024, 1, 1),
    to=datetime(2024, 12, 31),
    message_ids=["msg_1", "msg_2"],
)  # -> MessageList

# Детали видео
details = await bot.get_video_attachment_details(...)  # -> VideoAttachmentDetails
```

### Chats API

```python
chat = await bot.get_chat(chat_id=123)  # -> Chat
chats = await bot.get_chats(...)        # -> список чатов
chat = await bot.get_chat_by_link(link="https://max.ru/chat/abc")  # -> Chat

members = await bot.get_members(
    chat_id=123,
    count=100,
    marker=None,
    user_ids=[1, 2, 3],
)  # -> ChatMembersList

member = await bot.get_membership(chat_id=123, user_id=456)  # -> ChatMember
admins = await bot.get_admins(chat_id=123)  # -> ChatAdminsList

await bot.add_members(chat_id=123, user_ids=[1, 2, 3])
await bot.remove_member(chat_id=123, user_id=1)
await bot.set_admins(chat_id=123, user_ids=[1, 2])
await bot.delete_admin(chat_id=123, user_id=1)

await bot.edit_chat(chat_id=123, ...)
await bot.delete_chat(chat_id=123)
await bot.leave_chat(chat_id=123)

await bot.pin_message(chat_id=123, message_id="msg_123")
await bot.unpin_message(chat_id=123, message_id="msg_123")
pinned = await bot.get_pinned_message(chat_id=123)

from maxo.enums import SenderAction
await bot.send_action(chat_id=123, action=SenderAction.TYPING)
```

### Subscriptions API

```python
await bot.subscribe(url="https://example.com/webhook", secret="secret", update_types=["message_created"])
await bot.unsubscribe(url="https://example.com/webhook")
subs = await bot.get_subscriptions()
updates = await bot.get_updates(limit=100, marker=None, timeout=30, types=None)
```

### Upload API

```python
url = await bot.get_upload_url()  # -> UploadEndpoint
result = await bot.upload_media(file=..., type=...)  # загрузка медиа
```

### Download

```python
await bot.download(
    url="https://...",
    destination=Path("/path/to/file"),  # или BinaryIO, или None (вернёт BytesIO)
    timeout=30,
    chunk_size=65536,
    seek=True,
)  # -> BinaryIO | None
```

### Прямой вызов методов

```python
from maxo.methods import SomeMethod
result = await bot.call_method(SomeMethod(...))
await bot.silent_call_method(SomeMethod(...))  # Без ошибки при сбое
```

---

## 5. FSM — Finite State Machine

### Определение состояний

```python
from maxo.fsm import State, StatesGroup

class Registration(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_bio = State()
```

Состояния автоматически получают имена: `Registration:waiting_name`.

**Вложенные группы:**
```python
class Parent(StatesGroup):
    parent_state = State()

    class Child(StatesGroup):
        child_state = State()
# Child state имеет имя: Parent.Child:child_state
```

**Мета-атрибуты StatesGroup:**
- `__states__` — кортеж состояний группы
- `__all_states__` — все состояния (включая вложенные)
- `__all_states_names__` — все имена состояний
- `__full_group_name__` — полное имя группы

**Специальные состояния:**
```python
from maxo.fsm.state import any_state, default_state

any_state = State("*")     # Матчит любое состояние
default_state = State()    # Состояние по умолчанию
```

### FSMContext — все методы

```python
from maxo.fsm import FSMContext

@dp.message_created()
async def handler(update: MessageCreated, fsm_context: FSMContext) -> None:
    # Установка состояния
    await fsm_context.set_state(Registration.waiting_name)

    # Получение состояния
    state = await fsm_context.get_state()  # -> "Registration:waiting_name" | None

    # Работа с данными
    await fsm_context.set_data({"name": "Иван", "age": 25})
    data = await fsm_context.get_data()  # -> {"name": "Иван", "age": 25}

    # Одно значение
    name = await fsm_context.get_value("name", default="Аноним")

    # Обновление данных (merge)
    updated = await fsm_context.update_data({"age": 30}, city="Москва")
    # updated = {"name": "Иван", "age": 30, "city": "Москва"}

    # Очистка (состояние + данные)
    await fsm_context.clear()
```

### StateFilter — фильтрация по состоянию

```python
from maxo.fsm import StateFilter

@dp.message_created(StateFilter(Registration.waiting_name))
async def process_name(update: MessageCreated, facade: MessageCreatedFacade, fsm_context: FSMContext) -> None:
    name = update.message.body.text
    await fsm_context.update_data(name=name)
    await fsm_context.set_state(Registration.waiting_age)

# Фильтрация по группе состояний:
@dp.message_created(StateFilter(Registration))  # Все состояния из Registration

# Фильтрация по нескольким состояниям:
@dp.message_created(StateFilter(Registration.waiting_name, Registration.waiting_age))
```

### Хранилища

**MemoryStorage** (по умолчанию, для разработки):
```python
from maxo.fsm.storages.memory import MemoryStorage
dp = Dispatcher(storage=MemoryStorage())
```
- Хранит в RAM, данные теряются при перезапуске.
- НЕ поддерживает multi-instance.

**RedisStorage** (для production, требует `pip install maxo[redis]`):
```python
from maxo.fsm.storages.redis import RedisStorage

# Из URL:
storage = RedisStorage.from_url("redis://localhost:6379/0")

# Или напрямую:
storage = RedisStorage(
    redis=redis_client,
    key_builder=DefaultKeyBuilder(),
    state_ttl=3600,      # TTL для состояний (секунды)
    data_ttl=7200,       # TTL для данных
    json_loads=json.loads,
    json_dumps=json.dumps,
)
dp = Dispatcher(storage=storage)
```

**Создание isolation для multi-instance:**
```python
isolation = storage.create_isolation(lock_kwargs={"timeout": 60})
dp = Dispatcher(storage=storage, events_isolation=isolation)
```

### Event Isolation

- `SimpleEventIsolation` — asyncio Lock (в памяти)
- `DisabledEventIsolation` — без блокировки
- `RedisEventIsolation` — Redis lock (для multi-instance)

### KeyBuilder

```python
from maxo.fsm.key_builder import DefaultKeyBuilder

# Для dialogs ОБЯЗАТЕЛЬНО with_destiny=True!
key_builder = DefaultKeyBuilder(with_destiny=True)
dp = Dispatcher(key_builder=key_builder)
```

**Параметры DefaultKeyBuilder:**
- `prefix: str = "fsm"` — префикс ключей
- `separator: str = ":"` — разделитель
- `with_bot_id: bool = False` — включать ID бота
- `with_destiny: bool = False` — включать destiny (для dialogs)

### StorageKey

```python
from maxo.fsm.key_builder import StorageKey

key = StorageKey(
    bot_id=123456,
    chat_id=789,
    user_id=456,
    destiny="default",
)
```

---

## 6. Фильтры — ВСЕ встроенные + создание своих

### 6.1. Command

```python
from maxo.routing.filters import Command, CommandStart

@dp.message_created(Command("start", "help"))  # Несколько команд
@dp.message_created(CommandStart())             # /start (алиас)
async def handler(update: MessageCreated, facade: MessageCreatedFacade) -> None:
    pass

# С параметрами:
Command(
    "start",
    prefix="/",           # Префикс команды
    ignore_case=False,    # Игнорировать регистр
    ignore_mention=False, # Игнорировать @mention
)

# С regexp:
Command(r"start_(\d+)", regexp=True)  # Регулярное выражение
```

**CommandObject** (данные команды, записываются в ctx):
```python
@dp.message_created(Command("start"))
async def handler(update: MessageCreated, ctx: Ctx, command: CommandObject) -> None:
    # command.prefix  # "/"
    # command.command # "start"
    # command.args    # аргументы после команды
    # command.mention # bool — было ли упоминание бота
    # command.text    # полный текст команды
    pass
```

### 6.2. StateFilter

```python
from maxo.fsm import StateFilter

@dp.message_created(StateFilter(MyStates.step1))
@dp.message_created(StateFilter(MyStates))  # Вся группа
```

### 6.3. MagicFilter

```python
from magic_filter import F
from maxo.integrations.magic_filter import MagicFilter

@dp.message_created(MagicFilter(F.text == "hello"))
@dp.message_created(MagicFilter(F.message.sender.first_name == "Kirill"))
@dp.message_callback(MagicFilter(F.payload == "my_callback"))
@dp.message_created(MagicFilter(F.text.casefold() == "отмена"))
```

### 6.4. ExceptionTypeFilter

```python
from maxo.routing.filters import ExceptionTypeFilter

@dp.error(ExceptionTypeFilter(ValueError))
async def value_error(event: ErrorEvent, facade: ErrorEventFacade) -> None:
    await facade.answer_text(f"Ошибка: {event.error}")

# use_subclass=True (по умолчанию) — включает подклассы:
ExceptionTypeFilter(ValueError, use_subclass=True)  # Ловит ValueError и подклассы
```

### 6.5. ExceptionMessageFilter

```python
from maxo.routing.filters import ExceptionMessageFilter

@dp.error(ExceptionMessageFilter(r"Access denied"))
async def access_denied(event: ErrorEvent, facade: ErrorEventFacade) -> None:
    pass
```

### 6.6. DeeplinkFilter

```python
from maxo.routing.filters import DeeplinkFilter

@dp.bot_started(DeeplinkFilter(deep_link_encoded=False))
async def deep_link_handler(update: BotStarted, facade: BotStartedFacade) -> None:
    payload = update.payload  # Данные из deep link
```

### 6.7. Payload (для callback)

```python
from maxo.routing.filters.payload import Payload

class MyCallback(Payload, prefix="my", sep="_"):
    action: str
    item_id: int

@dp.message_callback(MyCallback.filter())
async def handler(update: MessageCallback, facade: MessageCallbackFacade) -> None:
    # Автоматический парсинг payload
    pass

# Упаковка:
cb_data = MyCallback(action="buy", item_id=42).pack()  # "my_buy_42"
```

### 6.8. Логические операторы

```python
from maxo.routing.filters import AndFilter, OrFilter, InvertFilter

# Операторы:
@dp.message_created(Command("admin") & MagicFilter(F.text == "secret"))  # И
@dp.message_created(Command("help") | Command("start"))                   # ИЛИ
@dp.message_created(~Command("ban"))                                      # НЕ

# Классы:
AndFilter(Command("admin"), MagicFilter(F.text == "secret"))
OrFilter(Command("help"), Command("start"))
InvertFilter(Command("ban"))

# Алиасы:
from maxo.routing.filters import and_f, or_f, invert_f
```

### 6.9. Создание своего фильтра

```python
from maxo.routing.filters import BaseFilter
from maxo.routing.ctx import Ctx
from maxo.routing.updates.message_created import MessageCreated

class MinLengthFilter(BaseFilter[MessageCreated]):
    def __init__(self, min_length: int):
        self.min_length = min_length

    async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
        text = update.message.body.text or ""
        if len(text) >= self.min_length:
            ctx["text_length"] = len(text)  # Запись в ctx для инжекта в handler
            return True
        return False

@dp.message_created(MinLengthFilter(10))
async def handler(update: MessageCreated, facade: MessageCreatedFacade, text_length: int) -> None:
    # text_length автоматически инжектируется из ctx
    await facade.answer_text(f"Длина: {text_length}")
```

**Важно:** Если фильтр возвращает `dict`, данные автоматически добавляются в `ctx`:
```python
class UserFilter(BaseFilter[MessageCreated]):
    async def __call__(self, update: MessageCreated, ctx: Ctx) -> dict | bool:
        if update.message.sender:
            return {"user_name": update.message.sender.first_name}
        return False

@dp.message_created(UserFilter())
async def handler(update: MessageCreated, user_name: str) -> None:
    # user_name инжектируется из dict, возвращённого фильтром
    pass
```

---

## 7. Middleware — ВСЕ детали

### 7.1. Два типа

- **Outer Middleware** — выполняется **ДО** фильтров (оборачивает весь процесс поиска обработчика)
- **Inner Middleware** — выполняется **ПОСЛЕ** фильтров, **ДО/ПОСЛЕ** обработчика

### 7.2. Поток выполнения

```
Update → Outer MW → Фильтры → Inner MW → Handler → Inner MW (после) → Outer MW (после)
```

### 7.3. Написание middleware

```python
from typing import Any
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.ctx import Ctx
from maxo.routing.updates.message_created import MessageCreated

class LoggingMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(
        self,
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        # ДО обработчика
        print(f"Получено сообщение: {update.message.body.text}")
        ctx["start_time"] = time.time()  # Данные в ctx

        result = await next(ctx)  # Вызов следующего middleware / обработчика

        # ПОСЛЕ обработчика
        duration = time.time() - ctx.get("start_time", 0)
        print(f"Обработка заняла: {duration:.2f}s")
        return result
```

### 7.4. Регистрация

```python
# Outer для всех message_created в dispatcher
dp.message_created.middleware.outer(LoggingMiddleware())

# Inner для callback в конкретном роутере
shop_router.message_callback.middleware.inner(TransactionMiddleware())
```

### 7.5. Данные из middleware

Данные, добавленные в `ctx`, автоматически инжектируются в аргументы обработчика **по имени**:

```python
class MyService:
    def greet(self, name: str) -> str:
        return f"Привет, {name}!"

class ServiceMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(self, update: MessageCreated, ctx: Ctx, next: NextMiddleware) -> Any:
        ctx["my_service"] = MyService()
        return await next(ctx)

dp.message_created.middleware.outer(ServiceMiddleware())

@dp.message_created()
async def handler(update: MessageCreated, my_service: MyService) -> None:
    # my_service автоматически инжектируется из ctx
    text = my_service.greet("мир")
    await facade.answer_text(text)
```

### 7.6. Встроенные middleware

Dispatcher автоматически регистрирует:

- `ErrorMiddleware` — try/except вокруг обработки, создаёт `ErrorEvent` при ошибке
- `UpdateContextMiddleware` — извлекает контекст обновления (`update_context`, `event_from_user`, `event_chat`, `event_context`)
- `FSMContextMiddleware` — создаёт `FSMContext` и управляет состоянием
- `FacadeMiddleware` — создаёт фасады для обработчиков

**Ключи в ctx:**
```python
# UpdateContextMiddleware:
UPDATE_CONTEXT_KEY = "update_context"
EVENT_FROM_USER_KEY = "event_from_user"
EVENT_CHAT_KEY = "event_chat"
EVENT_CONTEXT_KEY = "event_context"

# FSMContextMiddleware:
FSM_STORAGE_KEY = "fsm_storage"
FSM_CONTEXT_KEY = "fsm_context"
FSM_CONTEXT_STATE_KEY = "state"
RAW_STATE_KEY = "raw_state"

# FacadeMiddleware:
FACADE_KEY = "facade"
```

### 7.7. HTTP-level middleware (Bot)

```python
from unihttp.middlewares.base import AsyncMiddleware

class RetryMiddleware(AsyncMiddleware):
    async def handle(self, request, next_handler) -> HTTPResponse:
        # Логика retry с backoff
        response = await next_handler(request)
        return response

bot = Bot(token, middleware=[RetryMiddleware()])
```

---

## 8. Фасады (Facades) — ВСЕ методы

Фасады автоматически инжектируются в обработчики по типу аргумента. Они знают контекст события (chat_id, user_id уже известны).

### 8.1. MessageCreatedFacade

```python
from maxo.utils.facades.updates.message_created import MessageCreatedFacade

@dp.message_created()
async def handler(update: MessageCreated, facade: MessageCreatedFacade) -> None:
    pass
```

**Свойства:**
- `facade.message` → `Message`
- `facade.chat_id` → `int`
- `facade.bot` → `Bot`

**Методы:**

| Метод | Параметры | Описание |
|-------|-----------|----------|
| `answer_text` | `text: str, keyboard=None, notify=Omitted(), format=Omitted(), disable_link_preview=Omitted()` | Быстрый ответ текстом |
| `reply_text` | те же | Ответ с reply-ссылкой на сообщение |
| `send_message` | `text=None, link=None, notify=True, format=Omitted(), disable_link_preview=Omitted(), keyboard=None, media=None` | Полная отправка |
| `send_media` | `media, text=None, keyboard=None, notify=Omitted(), format=Omitted(), link=None, disable_link_preview=Omitted()` | Отправка медиа |
| `edit_message` | `text=None, keyboard=None, media=None, link=None, notify=True, format=Omitted()` | Редактирование |
| `delete_message` | — | Удаление → `SimpleQueryResult` |
| `get_chat` | — | Получить `Chat` |
| `get_members` | `count=Omitted(), marker=Omitted(), user_ids=Omitted()` | Получить `ChatMembersList` |
| `leave_chat` | — | Покинуть чат → `SimpleQueryResult` |
| `get_message_by_id` | `message_id: str` | Получить `Message` |

### 8.2. MessageCallbackFacade

Всё из `MessageCreatedFacade` + `CallbackMethodsFacade`:

| Метод | Параметры | Описание |
|-------|-----------|----------|
| `callback_answer` | `notification=Omitted(), message=None` | Ответ на callback |

**Свойства:**
- `facade.callback` → `Callback`

### 8.3. BotStartedFacade

| Свойства | `chat_id: int`, `user: User`, `payload: Omittable[str \| None]`, `user_locale: Omittable[str]` |
| Наследует | `ChatMethodsFacade` |

### 8.4. ChatMethodsFacade (общая для нескольких фасадов)

| Метод | Параметры | Возвращает |
|-------|-----------|------------|
| `send_message` | `text=None, link=None, notify=True, format=Omitted(), disable_link_preview=Omitted(), keyboard=None, media=None` | `Message` |
| `get_chat` | — | `Chat` |
| `get_members` | `count=Omitted(), marker=Omitted(), user_ids=Omitted()` | `ChatMembersList` |
| `leave_chat` | — | `SimpleQueryResult` |
| `get_messages` | `count=Omitted(), from_=Omitted(), message_ids=Omitted(), to=Omitted()` | `MessageList` |

### 8.5. BotMethodsFacade

| Метод | Параметры | Возвращает |
|-------|-----------|------------|
| `get_my_info` | — | `BotInfo` |
| `edit_bot_info` | `first_name=Omitted(), last_name=Omitted(), description=Omitted(), commands=Omitted(), photo=Omitted()` | `BotInfo` |

### 8.6. MediaInput — отправка медиа

```python
from maxo.utils.facades.methods.attachments import MediaInput
# MediaInput = InputFile | MediaAttachmentsRequests
```

**Загрузка файла:**
```python
from maxo.utils.upload_media import BufferedInputFile

photo = BufferedInputFile.image(content_bytes, "photo.jpg")
await facade.send_media(media=photo, text="Новое фото")
```

**По токену:**
```python
from maxo.types import PhotoAttachmentRequest

photo = PhotoAttachmentRequest.factory(token="upload_token")
await facade.send_media(media=photo, text="Фото")
```

**Микс:**
```python
media = [
    BufferedInputFile.image(content, "photo.jpg"),
    VideoAttachmentRequest.factory(token=video_token),
]
await facade.send_message(text="Микс медиа", media=media)
```

### 8.7. Omitted паттерн

```python
from maxo.omit import Omitted, Omittable, is_omitted, is_not_omitted, is_defined, is_not_defined

# Omitted() → поле НЕ включается в запрос (сервер использует default)
# None → поле отправляется как null
# "value" → поле отправляется со значением

await facade.answer_text("Привет!")                    # notify=Omitted → сервер использует default (true)
await facade.answer_text("Тихое", notify=False)        # notify=False → явно false в запрос
await facade.answer_text("Без уведомления", notify=None)  # notify=None → явно null в запрос
```

**Проверки:**
```python
value: int | None | Omitted = get_value()

if is_omitted(value):
    print("Не передано")
elif value is None:
    print("Передано None")
else:
    print(f"Значение: {value}")

# Для mypy type narrowing:
if is_defined(value):
    print(f"Точно число: {value + 1}")  # mypy знает, что value — int

# unsafe_ свойства — бросают AttributeIsEmptyError если поле пустое:
from maxo.exceptions import AttributeIsEmptyError
try:
    name = update.message.unsafe_sender.first_name
except AttributeIsEmptyError:
    name = "Аноним"
```

---

## 9. Диалоги (maxo.dialogs) — ПОЛНОЕ руководство

Портировано из `aiogram_dialog`. Мощная система UI-сценариев поверх FSM.

### 9.1. Основные компоненты

- **Dialog** — объединение окон в сценарий
- **Window** — одно сообщение бота с виджетами
- **DialogManager** — управление переходами
- **setup_dialogs** — инициализация диалогов

### 9.2. Инициализация

```python
from maxo.dialogs import setup_dialogs

dp = Dispatcher(key_builder=DefaultKeyBuilder(with_destiny=True))  # Обязательно!
setup_dialogs(dp)
```

**Для тестирования:**
```python
from maxo.dialogs.test_tools import MockMessageManager
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage

storage = JsonMemoryStorage()
mm = MockMessageManager()
dp = Dispatcher(storage=storage, key_builder=DefaultKeyBuilder(with_destiny=True))
setup_dialogs(dp, message_manager=mm)
```

### 9.3. Определение диалога

```python
from maxo.dialogs import Dialog, Window, DialogManager, StartMode, ShowMode
from maxo.dialogs.widgets.text import Const, Format, Multi
from maxo.dialogs.widgets.kbd import Back, Button, SwitchTo, Next
from maxo.dialogs.widgets.input import TextInput
from maxo.dialogs.widgets.media import StaticMedia

class DialogSG(StatesGroup):
    greeting = State()
    age = State()
    finish = State()

# Getter — функция получения данных в окно
async def get_data(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"name": dialog_manager.dialog_data.get("name", "Аноним")}

dialog = Dialog(
    Window(
        Const("Привет! Представься:"),
        TextInput(id="name_handler", on_success=name_handler),
        state=DialogSG.greeting,
    ),
    Window(
        Format("{name}! Сколько тебе лет?"),
        Button(Const("18-25"), id="age_btn", on_click=on_age),
        state=DialogSG.age,
        getter=get_data,
    ),
    Window(
        Multi(Format("{name}! Спасибо."), Const("Не куришь", when="can_smoke"), sep="\n\n"),
        Row(Back(), SwitchTo(Const("Заново"), id="restart", state=DialogSG.greeting)),
        getter=get_data,
        state=DialogSG.finish,
    ),
    on_start=async_fn,            # Колбек при запуске диалога
    on_close=async_fn,            # Колбек при закрытии
    on_process_result=async_fn,   # Колбек при возврате результата
    getter=common_getter,         # Общий геттер для всех окон
    preview_data=preview_getter,  # Данные для превью
)

@dp.message_created(CommandStart())
async def start(update: MessageCreated, manager: DialogManager) -> None:
    await manager.start(DialogSG.greeting, mode=StartMode.RESET_STACK)

dp.include(dialog)
setup_dialogs(dp)
```

### 9.4. Dialog — все параметры

```python
Dialog(
    *windows: Window,                 # Окна диалога
    on_start: OnDialogEvent | None = None,         # (manager: DialogManager, start_data: Data) -> None
    on_close: OnDialogEvent | None = None,         # (result: Any, manager: DialogManager) -> None
    on_process_result: OnResultEvent | None = None,  # (start_data: Data, result: Any, manager: DialogManager) -> Any
    launch_mode: LaunchMode = LaunchMode.STANDARD, # Режим запуска
    getter: GetterVariant = None,                  # Общий геттер
    preview_data: GetterVariant = None,            # Данные для превью
    name: str | None = None,                       # Имя диалога
)
```

### 9.5. Window — все параметры

```python
Window(
    *widgets: WidgetSrc,              # Виджеты (текст, кнопки, медиа, input)
    state: State,                     # FSM-состояние (ОБЯЗАТЕЛЬНО)
    getter: GetterVariant = None,     # Локальный геттер
    on_process_result: OnResultEvent | None = None,
    markup_factory: MarkupFactory = InlineKeyboardFactory(),
    parse_mode: TextFormat | None = None,            # Формат текста
    disable_web_page_preview: bool | None = None,    # DEPRECATED, используй LinkPreview
    protect_content: bool | None = None,
    preview_add_transitions: list[Keyboard] | None = None,  # Для диаграммы переходов
    preview_data: GetterVariant = None,
)
```

### 9.6. DialogManager — все методы

```python
from maxo.dialogs import DialogManager

@dp.message_created(CommandStart())
async def start(update: MessageCreated, manager: DialogManager) -> None:
    # Запуск диалога
    await manager.start(DialogSG.greeting, data={"key": "value"}, mode=StartMode.RESET_STACK)

# Все методы DialogManager:
await manager.start(state, data=None, mode=StartMode.NORMAL, show_mode=None, access_settings=None)
await manager.switch_to(state, show_mode=None)   # Переключить окно
await manager.next(show_mode=None)                # Следующее окно
await manager.back(show_mode=None)                # Предыдущее окно
await manager.done(result=None, show_mode=None)   # Закрыть диалог
await manager.update(data=None, show_mode=None)   # Обновить данные и перерисовать
await manager.answer_callback()                   # Ответить на callback
await manager.reset_stack(remove_keyboard=True)   # Сбросить стек

manager.find(widget_id)          # Найти виджет по ID
manager.current_context()        # Текущий контекст
manager.has_context()            # Есть ли контекст
manager.current_stack()          # Текущий стек
manager.storage()                # StorageProxy

manager.dialog_data            # Мутируемый dict данных диалога
manager.start_data             # Неизменяемые данные запуска
manager.middleware_data        # Данные из middleware
manager.event                  # Текущее событие
manager.show_mode              # ShowMode (get/set)
manager.disabled               # bool — отключён ли менеджер

manager.is_preview()           # bool — это превью?
manager.is_event_simulated()   # bool — это симуляция?

manager.dialog()               # DialogProtocol
manager.bg(user_id=None, chat_id=None, stack_id=None, load=False)  # -> BaseDialogManager

async with manager.fg() as fg_manager:  # Foreground manager (контекстный)
    await fg_manager.start(DialogSG.other)

await manager.mark_closed()      # Отметить как закрытый
await manager.close_manager()    # Закрыть менеджер
await manager.load_data()        # Загрузить данные
```

### 9.7. StartMode

| Режим | Описание |
|-------|----------|
| `StartMode.NORMAL` | Поверх текущего стека (по умолчанию) |
| `StartMode.RESET_STACK` | Очистить стек перед запуском |
| `StartMode.NEW_STACK` | Новый параллельный стек |

### 9.8. ShowMode

| Режим | Описание |
|-------|----------|
| `ShowMode.AUTO` | SEND для новых, EDIT для обновлений (по умолчанию) |
| `ShowMode.EDIT` | Редактировать сообщение |
| `ShowMode.SEND` | Отправить новое |
| `ShowMode.DELETE_AND_SEND` | Удалить и отправить |
| `ShowMode.NO_UPDATE` | Не обновлять |

### 9.9. ТЕКСТОВЫЕ ВИДЖЕТЫ

```python
from maxo.dialogs.widgets.text import Const, Format, Jinja, Multi, Case, Progress, List, ScrollingText
```

| Виджет | Параметры | Описание |
|--------|-----------|----------|
| `Const("Текст")` | `text: str` | Статический текст |
| `Format("Привет, {name}!")` | `template: str` | Форматирование из getter/dialog_data |
| `Jinja("Привет, {{ user.name }}!")` | `template: str` | Jinja2 шаблон |
| `Multi(Const(...), Format(...), sep="\n")` | `*TextWidget, sep: str` | Несколько текстов |
| `Case(texts={"en": Const("Hi"), "ru": Const("Привет")}, selector="lang")` | `texts: dict, selector: str` | Выбор по ключу |
| `Progress(value, width=10)` | `value: float [0-1]` | Прогресс-бар |
| `List(items="items", separator="\n")` | `items: str-key, separator: str` | Список элементов |
| `ScrollingText(...)` | — | Скроллящийся текст |

### 9.10. КЛАВИАТУРНЫЕ ВИДЖЕТЫ

```python
from maxo.dialogs.widgets.kbd import (
    Button, Url, Clipboard, WebApp,
    Row, Column, Group,
    Select, Radio, Toggle, Multiselect, Checkbox, Counter,
    ListGroup, ScrollingGroup,
    Calendar, TimeSelect,
    Next, Back, Cancel, SwitchTo, Start,
    RequestContact, RequestLocation,
    FirstPage, PrevPage, NextPage, LastPage, SwitchPage, NumberedPager,
    CurrentPage, StubScroll,
)
```

| Виджет | Параметры | Описание |
|--------|-----------|----------|
| `Button(text, id, on_click, when)` | `text: TextWidget, id: str, on_click: callback, when: str-key` | Callback-кнопка |
| `Url(text, url, when)` | `url: TextWidget` | URL-кнопка |
| `Clipboard(text, payload, when)` | `payload: TextWidget` | Копирование в буфер |
| `WebApp(text, url, when)` | `url: TextWidget` | WebApp кнопка |
| `Row(btn1, btn2)` | `*KeyboardWidget` | Кнопки в строку |
| `Column(btn1, btn2)` | `*KeyboardWidget` | Кнопки в столбец |
| `Group(btn1, btn2, btn3, width=2)` | `*KeyboardWidget, width: int` | Сетка кнопок |

**Select:**
```python
Select(
    Format("{item[1]}"),
    id="sel",
    item_id_getter=lambda x: x[0],
    items="fruits",          # Ключ из getter данных
    on_click=on_fruit_click,
    when=None,               # Условие видимости (ключ из данных)
)
```

**Radio:**
```python
Radio(
    Format("✅ {item[1]}"),    # Текст когда выбран
    Format("  {item[1]}"),    # Текст когда не выбран
    id="radio",
    item_id_getter=lambda x: x[0],
    items="fruits",
    on_click=on_radio_click,
)
```

**Checkbox:**
```python
Checkbox(
    Const("ON"),
    Const("OFF"),
    id="chk",
    default=False,
    on_state_changed=on_checkbox_change,
)
```

**Counter:**
```python
Counter(
    id="counter",
    default=0,
    min_value=0,
    max_value=100,
    increment=1,
    on_click=on_counter_click,
    # Текстовые виджеты для кнопок:
    plus_text=Const("+"),
    minus_text=Const("-"),
    value_text=Format("{value}"),
)
```

**ListGroup:**
```python
ListGroup(
    Button(Format("{item[name]} - {item[price]} ₽"), id="i", on_click=on_item_click),
    id="products",
    item_id_getter=lambda x: x["id"],
    items=lambda d: d["items"],  # Или строка-ключ
    # Пагинация:
    page_size=10,
    on_page_changed=on_page_click,
    # Pager-виджеты:
    pager=NumberedPager(...),
)
```

**Calendar:**
```python
Calendar(
    id="calendar",
    on_click=on_date_click,
    # Настройки:
    firstweekday=Calendar.START_WEEKDAY_MONDAY,
    shown_weeks=6,
    # Тексты:
    title_format=Format("{date: %B %Y}"),
    weekday_texts=(Const("Пн"), Const("Вт"), ...),
    header_format=Format("{date: %d}"),
    today_text=Const("●"),
)
```

**TimeSelect:**
```python
TimeSelect(
    id="time",
    hour_header=Const("Hour"),
    minute_header=Const("Minute"),
    button_text=Format("{value}"),
    button_selected_text=Format("[{value}]"),
    on_hour_click=None,
    on_minute_click=None,
    on_value_changed=None,  # (event, widget, manager, value: time)
    hour_width=6,
    minute_precision=5,
    minute_width=6,
)
```

**Навигационные кнопки:**

| Виджет | Описание |
|--------|----------|
| `Next(text, id, when)` | Следующее окно |
| `Back(text, id, when)` | Предыдущее окно |
| `Cancel(text, id, when)` | Закрыть диалог |
| `SwitchTo(text, id, state, when)` | Перейти к конкретному State |
| `Start(text, id, state, mode=StartMode.NORMAL, when)` | Запустить новый диалог |

**Pager-виджеты:**

| Виджет | Описание |
|--------|----------|
| `FirstPage(text, id, ...)` | Первая страница |
| `PrevPage(text, id, ...)` | Предыдущая |
| `NextPage(text, id, ...)` | Следующая |
| `LastPage(text, id, ...)` | Последняя |
| `SwitchPage(text, id, page, ...)` | На конкретную страницу |
| `NumberedPager(id, ...)` | Нумерованный pager |
| `CurrentPage(...)` | Текущая страница (текст) |
| `StubScroll(id, total_pages=10)` | Заглушка скролла |

**Request-кнопки:**
| Виджет | Описание |
|--------|----------|
| `RequestContact(text, when)` | Запрос контакта |
| `RequestLocation(text, when)` | Запрос геолокации |

### 9.11. INPUT-виджеты

```python
from maxo.dialogs.widgets.input import TextInput, ManagedTextInput, MessageInput
```

**TextInput:**
```python
TextInput(
    id="name_handler",
    on_success=async_fn,  # (message: MessageCreated, widget: ManagedTextInput, manager: DialogManager) -> Any
    on_error=None,        # (message, widget, manager, exception) -> Any
    filter=None,          # Фильтр для валидации
    # Настройки:
    type_factory=None,    # Функция преобразования
)
```

**MessageInput** (fallback для нетекстовых сообщений):
```python
MessageInput(
    on_message=async_fn,  # (message: MessageCreated, widget, manager) -> Any
)
```

### 9.12. МЕДИА-виджеты

```python
from maxo.dialogs.widgets.media import StaticMedia, DynamicMedia
```

| Виджет | Параметры | Описание |
|--------|-----------|----------|
| `StaticMedia(url="...", type="photo")` | `url: str, type: str` | Статическое медиа |
| `DynamicMedia(id="media")` | `id: str` | Динамическое медиа (URL из getter) |

### 9.13. LinkPreview

```python
from maxo.dialogs.widgets.link_preview import LinkPreview

LinkPreview(
    is_disabled=False,
    url=None,
    prefer_large_media=None,
    show_above_text=None,
)
```

### 9.14. Геттеры

Геттер — функция, возвращающая `dict`. Данные объединяются из геттера диалога и окна.

```python
async def my_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {"name": dialog_manager.dialog_data.get("name", "Аноним")}

# В окне:
Window(Format("Привет, {name}!"), state=SG.main, getter=my_getter)

# В диалоге (общий для всех окон):
Dialog(window, getter=common_getter)
```

**GetterVariant** = `Callable[..., dict] | Sequence[Callable[..., dict]] | None`

### 9.15. BgManagerFactory (фоновое управление)

```python
from maxo.dialogs.api.protocols import BgManagerFactory

bg_factory: BgManagerFactory = manager.middleware_data["dialog_bg_factory"]

# Создание менеджера для конкретного пользователя/чата
bg = bg_factory.bg(bot=bot, chat_id=chat_id, user_id=user_id)

# Фоновое управление
await bg.start(SG.main)              # Запуск диалога
await bg.update({"status": "done"})  # Обновление UI
await bg.done()                      # Закрытие
```

### 9.16. Превью диалогов

```python
from maxo.dialogs.tools.preview import render_preview, render_preview_content
from maxo.dialogs.tools.transitions import render_transitions

# HTML-превью
await render_preview(router, "preview.html")
html = await render_preview_content(router, simulate_events=True)

# Диаграмма переходов (требует graphviz)
render_transitions(router, title="Мой бот", filename="transitions", format="png")
```

**CLI:**
```bash
maxo-dialog-preview path/to/module.py:router_variable
```

**preview_add_transitions** для Window:
```python
Window(
    ...,
    preview_add_transitions=[
        Button(Const("Далее"), id="next", on_click=...),
        SwitchTo(Const("Настройки"), id="settings", state=SettingsSG.main),
    ],
)
```

### 9.17. Тестирование диалогов

```python
from maxo.dialogs.test_tools import BotClient, MockMessageManager
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.dialogs.test_tools.keyboard import InlineButtonTextLocator, InlineButtonPositionLocator, InlineButtonDataLocator
from maxo.fsm.key_builder import DefaultKeyBuilder

# Настройка
storage = JsonMemoryStorage()
mm = MockMessageManager()
dp = Dispatcher(storage=storage, key_builder=DefaultKeyBuilder(with_destiny=True))
setup_dialogs(dp, message_manager=mm)

# Создание клиента
client = BotClient(dp, user_id=1, chat_id=1)

# Отправка команды
await client.send("/start")

# Проверка сообщения
msg = mm.last_message()
assert "Главное меню" in msg.body.text

# Клик по кнопке
callback_id = await client.click(msg, InlineButtonTextLocator("Подробнее"))
mm.assert_answered(callback_id)

# Клик по позиции
await client.click(msg, InlineButtonPositionLocator(row=0, column=0))

# Клик по regex
await client.click(msg, InlineButtonDataLocator(r"action_.*"))

# Сброс истории
mm.reset_history()
```

### 9.18. Поддиалоги

```python
main_dialog = Dialog(
    Window(
        Const("Главное меню"),
        Start(Const("Настройки"), id="settings", state=SettingsSG.menu),
        state=MainSG.menu,
    ),
)

settings_dialog = Dialog(
    Window(
        Const("Настройки"),
        Cancel(Const("← Назад")),
        state=SettingsSG.menu,
    ),
)

dp.include(main_dialog, settings_dialog)
```

### 9.19. LaunchMode

```python
from maxo.dialogs import LaunchMode

LaunchMode.STANDARD   # Обычный режим (стек)
LaunchMode.EXCLUSIVE  # Только один экземпляр (старый закрывается)
LaunchMode.ROOT       # Корневой (все стеки закрываются)
```

### 9.20. CancelEventProcessing

```python
from maxo.dialogs import CancelEventProcessing

# Выбросить из callback обработчика для отмены обработки события
raise CancelEventProcessing()
```

### 9.21. UnsetId

```python
from maxo.dialogs import UnsetId

# Специальное значение для "без ID"
```

---

## 10. Клавиатуры (KeyboardBuilder)

```python
from maxo.utils.builders import KeyboardBuilder
```

### Все методы

| Метод | Параметры | Описание |
|-------|-----------|----------|
| `add_callback(text, payload)` | `text: str, payload: str` | Callback-кнопка |
| `add_link(text, url)` | `text: str, url: str` | Ссылка |
| `add_message(text)` | `text: str` | Кнопка с сообщением |
| `add_clipboard(text, payload)` | `text: str, payload: str` | Копирование в буфер |
| `add_request_contact(text)` | `text: str` | Запрос контакта |
| `add_request_geo_location(text, quick=Omitted())` | `text: str, quick: Omittable[bool]` | Запрос геолокации |
| `add(*buttons)` | `*InlineButtons` | Добавить любые кнопки |
| `row(*buttons, width=None)` | `width: int` | Новый ряд |
| `adjust(*sizes, repeat=False)` | `*int, repeat: bool` | Разбить по размерам |
| `attach(builder)` | `KeyboardBuilder` | Присоединить другой builder |
| `build()` | — | `Sequence[Sequence[InlineButtons]]` |

**Ограничения:**
- Макс. 7 кнопок в ряду
- Макс. 210 кнопок всего

### Пример

```python
keyboard = (
    KeyboardBuilder()
    .add_callback(text="Колбэк", payload="click_me")
    .add_link(text="Ссылка", url="https://example.com")
    .add_message(text="Сообщение")
    .add_clipboard(text="Копировать", payload="text_to_copy")
    .add_request_contact(text="Контакт")
    .add_request_geo_location(text="Геолокация")
    .adjust(2, 2, 1, 1)  # 2, 2, 1, 1 кнопки по рядам
    .build()
)
await facade.answer_text("Клавиатура", keyboard=keyboard)
```

### MagicFilter для callback

```python
from magic_filter import F
from maxo.integrations.magic_filter import MagicFilter

@dp.message_callback(MagicFilter(F.payload == "click_me"))
async def handler(update: MessageCallback, facade: MessageCallbackFacade) -> None:
    await facade.callback_answer("Кнопка нажата!")
```

---

## 11. Интеграции

### 11.1. Dishka (DI)

```bash
pip install maxo[dishka]
```

```python
from dishka import Provider, Scope, make_async_container, provide, FromDishka
from maxo.integrations.dishka import setup_dishka

class AppProvider(Provider):
    scope = Scope.APP

    @provide
    def greeter(self) -> GreeterService:
        return GreeterService()

container = make_async_container(AppProvider())
setup_dishka(container, dp, auto_inject=True)
```

**auto_inject=True** — зависимости инжектятся по типу аргумента:
```python
async def handler(message: MessageCreated, facade: MessageCreatedFacade, greeter: GreeterService) -> None:
    text = greeter.greet("мир")
    await facade.answer_text(text)
```

**auto_inject=False** — нужен `FromDishka` или `@inject`:
```python
async def handler(message: MessageCreated, facade: MessageCreatedFacade, greeter: FromDishka[GreeterService]) -> None:
    ...

# Или @inject:
from maxo.integrations.dishka import inject

@inject
async def handler(message: MessageCreated, facade: MessageCreatedFacade, greeter: GreeterService) -> None:
    ...
```

**MaxoProvider** — встроенный провайдер, предоставляет:
- `Bot`, `Dispatcher`, `UpdateContext`, `BaseStorage`, `FSMContext`, `RawState`, `MaxoUpdate`, `Ctx`

**DishkaMiddleware:**
```python
from maxo.integrations.dishka import DishkaMiddleware, CONTAINER_NAME

# Автоматически создаёт sub-container на каждый update
# В middleware можно получить контейнер:
class MyMiddleware(BaseMiddleware[MessageCreated]):
    async def __call__(self, update: MessageCreated, ctx: Ctx, next: NextMiddleware) -> Any:
        container = ctx.get(CONTAINER_NAME)
        service = await container.get(GreeterService)
        ctx["greeting"] = service.greet("гость")
        return await next(ctx)
```

**inject_handler / inject_router:**
```python
from maxo.integrations.dishka import inject_handler, inject_router

inject_router(router)  # Инъекция для всех обработчиков роутера
inject_handler(handler)  # Инъекция для конкретной функции
```

### 11.2. Magic Filter

```bash
pip install maxo[magic_filter]
```

```python
from magic_filter import F
from maxo.integrations.magic_filter import MagicFilter

@dp.message_created(MagicFilter(F.text == "hello"))
@dp.message_created(MagicFilter(F.message.sender.first_name == "Kirill"))
@dp.message_callback(MagicFilter(F.payload == "my_callback"))
```

---

## 12. Обработка ошибок

```python
from maxo.errors import ErrorEvent, MaxoError
from maxo.routing.filters import ExceptionTypeFilter, ExceptionMessageFilter

# Своё исключение:
class InvalidAge(MaxoError):
    message: str

# Выброс из обработчика:
@dp.message_created(Command("age"))
async def handle_age(message: MessageCreated, facade: MessageCreatedFacade) -> None:
    age = int(message.message.body.text or "0")
    if age < 0:
        raise InvalidAge("Возраст не может быть отрицательным")

# Глобальный обработчик:
@dp.error()
async def handle_all(event: ErrorEvent, facade: ErrorEventFacade) -> None:
    await facade.answer_text(f"Произошла ошибка: {event.error!r}")

# Фильтрация по типу:
@dp.error(ExceptionTypeFilter(InvalidAge))
async def handle_invalid_age(event: ErrorEvent[InvalidAge, MessageCreated], facade: ErrorEventFacade) -> None:
    await facade.answer_text(f"Ошибка: {event.error.message}")

# Фильтрация по сообщению:
@dp.error(ExceptionMessageFilter(r"Access denied"))
async def access_denied(event: ErrorEvent, facade: ErrorEventFacade) -> None:
    await facade.answer_text("Доступ запрещён")
```

---

## 13. Форматирование текста

```python
from maxo.utils.formatting import (
    Bold, Italic, Underline, Strikethrough, Monospaced,
    Heading, Highlighted, BlockQuote,
    Link, Mention, Text,
    as_line, as_list, as_marked_list, as_numbered_list,
    as_section, as_marked_section, as_numbered_section,
    as_key_value,
)
from maxo.enums import TextFormat
```

### Классы разметки

| Класс | HTML | Markdown |
|-------|------|----------|
| `Bold("текст")` | `<b>текст</b>` | `**текст**` |
| `Italic("текст")` | `<i>текст</i>` | `_текст_` |
| `Underline("текст")` | `<u>текст</u>` | `++текст++` |
| `Strikethrough("текст")` | `<s>текст</s>` | `~~текст~~` |
| `Monospaced("текст")` | `<code>текст</code>` | ````текст```` |
| `BlockQuote("текст")` | `<blockquote>текст</blockquote>` | — |
| `Heading("текст")` | — | `# текст` |
| `Highlighted("текст")` | — | `==текст==` |
| `Link("текст", url="https://...")` | `<a href="url">текст</a>` | `[текст](url)` |
| `Mention("Имя", user_id=123)` | `<a href="max://user/123">Имя</a>` | `[Имя](max://user/123)` |

### Методы

```python
text = Bold("Важное ", Italic("сообщение"), "!")
text.as_html()     # "<b>Важное <i>сообщение</i>!</b>"
text.as_markdown() # "**Важное _сообщение_!**"
text.as_kwargs()   # {"text": "...", "format": None}
```

### Вспомогательные функции

```python
as_line(Bold("Заголовок"), Italic("текст"), end="\n", sep="")
as_list("элемент 1", "элемент 2", sep="\n")
as_marked_list("элемент 1", "элемент 2", marker="- ")
as_numbered_list("элемент 1", "элемент 2", start=1, fmt="{}. ")
as_section(Bold("Заголовок"), "текст 1", "текст 2")
as_marked_section(Bold("Заголовок"), "пункт 1", "пункт 2", marker="- ")
as_key_value(Bold("Ключ"), "Значение")
```

---

## 14. Транспорт

### 14.1. Long Polling

```python
from maxo.transport.long_polling import LongPolling

# Блокирующий:
LongPolling(dp).run(
    bot,
    timeout=30,
    limit=100,
    marker=None,
    types=None,                    # ["message_created", ...]
    auto_close_bot=True,
    drop_pending_updates=False,
)

# Async:
await LongPolling(dp).start(bot)
```

**Важно:** Запуск нескольких процессов с Long Polling = дублирование обновлений! Для production используйте Webhook.

### 14.2. Webhook (FastAPI)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from maxo.collect_used_updates import collect_used_updates
from maxo.transport.webhook.engines import SimpleEngine
from maxo.transport.webhook.adapters.fastapi import FastApiWebAdapter
from maxo.transport.webhook.routing import StaticRouting
from maxo.transport.webhook.security import Security, StaticSecretToken

engine = SimpleEngine(
    dp, bot,
    web_adapter=FastApiWebAdapter(),
    routing=StaticRouting(url="https://example.com/webhook"),
    security=Security(secret_token=StaticSecretToken("secret")),
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    engine.register(app)
    await engine.on_startup(app)
    yield
    await engine.on_shutdown(app)

app = FastAPI(lifespan=lifespan)

@dp.after_startup()
async def on_startup(dispatcher: Dispatcher, webhook_engine: WebhookEngine) -> None:
    await webhook_engine.set_webhook(update_types=collect_used_updates(dispatcher))
```

### 14.3. Webhook (aiohttp)

Аналогично через `AiohttpWebAdapter()` и `web.run_app()`.

---

## 15. Утилиты

### 15.1. Upload Media

```python
from maxo.utils.upload_media import BufferedInputFile, FSInputFile

# Из байтов:
photo = BufferedInputFile.image(content_bytes, "photo.jpg")
video = BufferedInputFile.video(content_bytes, "video.mp4")
audio = BufferedInputFile.audio(content_bytes, "audio.mp3")
doc = BufferedInputFile.file(content_bytes, "document.pdf")

# Из файла:
photo = FSInputFile.image("./files/photo.jpg")
file = FSInputFile.file("files/doc.txt")
audio = FSInputFile.audio("./files/audio.mp3")
video = FSInputFile.video("./files/video.mp4")
```

### 15.2. Enums

```python
from maxo.enums import (
    TextFormat,        # HTML, MARKDOWN
    UpdateType,        # Все типы обновлений
    ButtonType,        # callback, link, message, clipboard, request_contact, request_geo_location, web_app
    AttachmentType,    # типы вложений
    ContentType,       # content type
    ChatType,          # personal, chat, channel
    ChatStatus,        # creator, admin, member, restricted, left, kicked
    ChatAdminPermission,
    SenderAction,      # TYPING и др.
    MessageLinkType,   # REPLY, FORWARD
    MarkupElementType,
    AttachmentRequestType,
    UploadType,
)
```

### 15.3. Ctx

```python
from maxo import Ctx

# Ctx — это MutableMapping[str, Any]
# Данные добавляются мидлварями и фильтрами, автоматически инжектируются в handler по имени
ctx["my_key"] = "value"
value = ctx.get("my_key", "default")
```

---

## 16. Полезные заметки и тонкости

### 16.1. Sender в каналах

При редактировании/удалении сообщений **в каналах** поле `sender` **отсутствует**. В ЛС/чатах — есть всегда.

```python
# Безопасный доступ:
if update.message.sender:  # Может быть Omitted
    name = update.message.sender.first_name
else:
    name = "Канал"

# Или через unsafe (бросает исключение если пусто):
try:
    name = update.message.unsafe_sender.first_name
except AttributeIsEmptyError:
    name = "Канал"
```

### 16.2. Бот должен быть админом

Для получения событий в чате/канале бот должен быть **администратором**.

### 16.3. Нет событий на изменение прав админа

Нет событий на повышение/понижение бота до админа.

### 16.4. Удаление чата

При удалении чата/канала приходит `UserRemovedFromChat`.

### 16.5. Лимиты медиа

- Максимум **12 медиа-аттачментов** в сообщении
- Файловый аттачмент — **только один**
- API принимает только **один файл** в сообщении (остальные по токенам)

### 16.6. FSM и multi-instance

Для работы в нескольких процессах используйте:
- `RedisStorage` вместо `MemoryStorage`
- `RedisEventIsolation` вместо `SimpleEventIsolation`
- `DefaultKeyBuilder(with_bot_id=True)` для изоляции по боту

### 16.7. Dialogs требуют with_destiny=True

```python
dp = Dispatcher(key_builder=DefaultKeyBuilder(with_destiny=True))
```

Без этого диалоги не будут работать корректно (конфликты состояний).

### 16.8. collect_used_updates

Для webhook используйте `collect_used_updates(dispatcher)` для отправки только нужных типов:

```python
from maxo.collect_used_updates import collect_used_updates

await webhook_engine.set_webhook(update_types=collect_used_updates(dp))
```

### 16.9. workflow_data

Передача ресурсов в обработчики через dispatcher:

```python
@dp.after_startup()
async def setup_redis() -> None:
    pool = redis.ConnectionPool.from_url("redis://localhost")
    dp.workflow_data["redis"] = redis.Redis(connection_pool=pool)

@dp.message_created()
async def handler(update: MessageCreated, redis: redis.Redis) -> None:
    # redis автоматически инжектируется из workflow_data
    pass
```

### 16.10. Порядок include = приоритет

```python
dp.include(important_router)  # Проверяется первым
dp.include(other_router)      # Проверяется вторым
```

Первый совпавший обработчик **останавливает** цепочку.

### 16.11. Сигналы вызывают ВСЕ обработчики

В отличие от обычных обработчиков, сигналы (`before_startup`, `after_startup`, etc.) вызывают **ВСЕ** зарегистрированные обработчики.

---

## 17. Чеклист для внесения изменений

### Код
- [ ] Все I/O операции async/await
- [ ] Полная типизация всех функций и методов
- [ ] Docstrings для публичных API
- [ ] Следование паттернам из существующего кода
- [ ] Использованы фасады вместо прямых вызовов бота (где возможно)
- [ ] Правильное использование Omitted для опциональных параметров

### FSM
- [ ] Для dialogs: `DefaultKeyBuilder(with_destiny=True)`
- [ ] `RedisStorage` для production, `MemoryStorage` для dev
- [ ] Состояния очищаются после завершения сценария

### Диалоги
- [ ] `setup_dialogs(dp)` вызван после include
- [ ] Все виджеты имеют уникальные `id`
- [ ] Getter'ы возвращают `dict`
- [ ] Preview-данные настроены для превью

### Тесты
- [ ] Написаны тесты для нового функционала
- [ ] Тесты диалогов через `BotClient` + `MockMessageManager`
- [ ] Все тесты проходят

### Code Quality
- [ ] Линтер без ошибок
- [ ] Форматирование применено

---

## 18. Связь с aiogram

maxo вдохновлён aiogram. Если что-то непонятно — можно смотреть аналогичные паттерны в aiogram:
- Роутеры, фильтры, мидлвари — аналогичная концепция
- FSM — очень похожий API
- Диалоги портированы из `aiogram_dialog` — документация aiogram_dialog полезна

---

## 19. Быстрая шпаргалка

### Эхо-бот (5 строк)
```python
from maxo import Bot, Dispatcher
from maxo.transport.long_polling import LongPolling

bot = Bot("TOKEN")
dp = Dispatcher()
dp.message_created()(lambda u, f: f.answer_text(u.message.body.text or "?"))
LongPolling(dp).run(bot)
```

### FSM-машина состояний
```python
class Form(StatesGroup):
    name = State()
    age = State()

@dp.message_created(CommandStart())
async def start(fsm: FSMContext, facade: MessageCreatedFacade):
    await fsm.set_state(Form.name)
    await facade.answer_text("Введи имя:")

@dp.message_created(StateFilter(Form.name))
async def get_name(update: MessageCreated, fsm: FSMContext, facade: MessageCreatedFacade):
    await fsm.update_data(name=update.message.body.text)
    await fsm.set_state(Form.age)
    await facade.answer_text("Введи возраст:")
```

### Callback + клавиатура
```python
kb = KeyboardBuilder().add_callback("Нажми", "my_action").build()
await facade.answer_text("Жми!", keyboard=kb)

@dp.message_callback(MagicFilter(F.payload == "my_action"))
async def on_click(facade: MessageCallbackFacade):
    await facade.callback_answer("Нажата!")
```

### Диалог за 30 секунд
```python
class SG(StatesGroup):
    main = State()

dialog = Dialog(Window(Const("Привет!"), state=SG.main))
dp.include(dialog)
setup_dialogs(dp)

@dp.message_created(CommandStart())
async def start(manager: DialogManager):
    await manager.start(SG.main, mode=StartMode.RESET_STACK)
```

---

*Последнее обновление: 13 апреля 2026*
