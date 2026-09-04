# AGENTS.md - правила разработки maxo для AI-агентов

Этот файл является единым источником правды для AI-агентов, работающих с
репозиторием `maxo`. Все инструкции, комментарии к разработке и
пользовательская документация для агентов в этом проекте пишутся на русском
языке.

`maxo` - асинхронный Python-фреймворк для разработки ботов российского
мессенджера MAX (`https://max.ru`). Текущая версия проекта: `0.8.3`.
Поддерживаемые версии Python: `3.12`, `3.13`, `3.14`.

## Единый источник инструкций

`AGENTS.md` - базовый и обязательный источник правил для всех AI-агентов.
`CLAUDE.md` должен оставаться симлинком на `./AGENTS.md`.

Не выноси обязательные правила в Claude-only skills или другие инструменты,
которые не читают Codex, Cursor, Copilot, Gemini и похожие агенты. Если
инструкции разрастутся, добавляй вложенные `AGENTS.md` ближе к области
ответственности - так уже сделано для кодогенерации (`butcher/AGENTS.md`);
по тому же принципу можно завести `src/maxo/bot/AGENTS.md`, `tests/AGENTS.md`
или `docs/AGENTS.md`.

Вложенный `AGENTS.md` дополняет корневой, а не заменяет: общие правила проекта
действуют и в подкаталоге. Рядом с ним держи симлинк `CLAUDE.md -> ./AGENTS.md`,
как в корне.

Специфичные файлы для отдельных инструментов допустимы только как тонкий слой
поверх `AGENTS.md`. В них нельзя держать единственную копию знаний о проекте.

## Рабочие команды

Проект использует `uv`. Сначала синхронизируй окружение:

```bash
uv sync --all-groups
```

Для CI-паритета используй прямые команды через `uv`:

```bash
uv run ruff check --no-fix .
uv run mypy --config-file pyproject.toml
uv run pytest tests/ --cov=src --cov-report=term
uv run nox -s test
```

Для точечного запуска:

```bash
uv run pytest tests/path/test_file.py::test_name -v
uv run ruff check --no-fix src/maxo/path.py tests/path/test_file.py
```

В дереве есть  `justfile`, и CI запускает линтеры и тесты именно через него.
Все рецепты сами вызывают `uv run`, поэтому активировать venv не нужно:

```bash
just lint       # ruff + codespell + slotscheck + bandit
just mypy
just test
just test-all
just all
just butcher       # генерация типов/enum'ов/методов по max-swagger.json
just butcher-test  # тесты самого генератора
```

Полезно помнить:

- `pyproject.toml` задает `ruff` c `fix = true`, поэтому для проверки без
  изменений используй `--no-fix`.
- Рецепт `just ruff` запускает `ruff check --fix .` и может менять файлы.
  Поэтому `lint.yml` зовет линтеры напрямую через `uv run`, а не через just:
  иначе CI чинил бы найденное и зеленел. Для проверки без правок локально -
  `uv run ruff check --no-fix .`.
- `just test` принимает дополнительные аргументы pytest, например
  `just test --cov-report=xml` (так делает CI) или `just test -k dialogs`.
- `pytest` в проекте работает с `asyncio_mode = auto`.
- CI проверяет lint на Python `3.14` и тесты на Python `3.12`, `3.13`, `3.14`
  с разрешением зависимостей `lowest-direct` и `highest`.
- `uv.lock` игнорируется в этом репозитории. Не добавляй его в коммит без
  отдельного решения мейнтейнера.

## Архитектура проекта

Ключевые директории:

| Путь                     | Назначение                                                                                                                        |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| `src/maxo/bot/`          | `Bot`, `MaxApiClient`, состояния бота, declarative Bot API methods на `unihttp`.                                                  |
| `src/maxo/types/`        | Типы MAX Bot API. Многие файлы сгенерированы по документации API.                                                                 |
| `src/maxo/enums/`        | Enum MAX Bot API. Многие файлы сгенерированы по документации API.                                                                 |
| `src/maxo/routing/`      | `Dispatcher`, `Router`, observers, handlers, filters, middlewares, facades и signals; `updates/` - устаревший слой совместимости. |
| `src/maxo/fsm/`          | FSM: `State`, `StatesGroup`, `FSMContext`, storage, isolation, key builders.                                                      |
| `src/maxo/dialogs/`      | Диалоги, портированные из `aiogram_dialog`: `Dialog`, `Window`, widgets, managers, preview, test tools.                           |
| `src/maxo/transport/`    | Long polling и webhook engine/adapters/routing/security.                                                                          |
| `src/maxo/errors/`       | Исключения публичного API и ошибки MAX Bot API.                                                                                   |
| `src/maxo/integrations/` | Интеграции `dishka` и `magic_filter`.                                                                                             |
| `src/maxo/utils/`        | Builders, upload helpers, formatting, deeplink/link helpers, facades.                                                             |
| `docs/`                  | Sphinx-документация на русском языке.                                                                                             |
| `examples/`              | Рабочие примеры использования публичного API.                                                                                     |
| `tests/`                 | Pytest-тесты по подсистемам.                                                                                                      |

Общая модель системы:

```text
Long polling / webhook
  -> Dispatcher
  -> Router tree
  -> outer middleware
  -> filters
  -> inner middleware
  -> handler
```

Ключевые паттерны:

- `Dispatcher` - корневой `Router`.
- `Router.include(...)` задает порядок обхода дочерних роутеров.
- Первый обработавший обычный update останавливает дальнейший поиск.
- Сигналы `before_startup`, `after_startup`, `before_shutdown`,
  `after_shutdown` обрабатываются как lifecycle hooks, а не как обычные update.
- `message`, `callback_query`, `edited_message` - алиасы для совместимости с
  привычками из aiogram.
- Facade и update-модели умеют отвечать через mixins после привязки бота.
- Флаги-маркеры хендлеров живут в `maxo.routing.flags`, инстанс `flags`
  экспортируется из top-level `maxo`.
- Для webhook используй `collect_used_updates(dispatcher)`, чтобы подписывать
  только реально используемые update types.
- Long polling находится в `maxo.transport.long_polling`. В docs и examples
  запускай его через `Dispatcher.run_polling` (свой event loop) или
  `Dispatcher.start_polling` (уже в асинхронном контексте). Класс `LongPolling`
  показывай только там, где нужен свой `backoff_config`.
- Поллинг не перехватывает `SIGINT` и `SIGTERM`, но глушит `KeyboardInterrupt`:
  остановкой процесса управляет приложение, а не фреймворк.
  Не добавляй такой перехват без отдельного решения мейнтейнера.
- Webhook находится в `maxo.transport.webhook`: engines, adapters, routing,
  security и per-bot config.

## Неочевидные паттерны и архитектурные решения

Эта секция описывает внутренние механизмы, которые нельзя понять, читая один
файл. Знание этих паттернов критично для правильной работы с проектом.

### Система типов MaxoType

**Метакласс автоматически применяет `@dataclass`**

`src/maxo/types/base.py` содержит `_MaxoTypeMetaClass`, который автоматически
превращает все классы, наследующие `MaxoType`, в dataclass:

```python
class Message(MaxoType):
    body: MessageBody  # автоматически становится kw_only полем
    recipient: Recipient
```

Эквивалентно:
```python
@dataclass(slots=True, frozen=False, kw_only=True)
class Message:
    ...
```

**Важно**: Если явно указать `__slots__`, метакласс не применит `@dataclass`.

**Автопривязка бота через BaseMethodsFacade**

Все `MaxoType` получают метод `as_(bot)` для привязки бота. В
`serialization.py` есть специальный loader, который автоматически привязывает
бот ко всем загруженным типам через `retort.extend(loader(...))`.

Это позволяет:
```python
message = update.message
await message.send_message(text="Reply")  # вместо bot.send_message(...)
```

**Паттерн `unsafe_*` для Omittable полей**

Для всех `Omittable[T]` полей должен быть `unsafe_*` property:

```python
class Message(MaxoType):
    sender: Omittable[User] = Omitted()

    @property
    def unsafe_sender(self) -> User:
        if is_defined(self.sender):
            return self.sender
        raise AttributeIsEmptyError(obj=self, attr="sender")
```

Используй `unsafe_*`, когда уверен, что поле присутствует. Это защищает от
`None`/`Omitted()` на уровне типов.

### Сериализация и полиморфизм

**TAG_PROVIDERS для union-типов**

`src/maxo/serialization.py` содержит `TAG_PROVIDERS` - список провайдеров для
полиморфной (де)сериализации:

```python
TAG_PROVIDERS = concat_provider(
    has_tag_provider(MessageCreated, "update_type", UpdateType.MESSAGE_CREATED),
    has_tag_provider(PhotoAttachment, "type", AttachmentType.IMAGE),
    # ...
)
```

При добавлении нового варианта в union-тип (новый update, attachment, button):

1. Создай класс, наследующий базовый тип
2. Добавь `has_tag_provider` в `TAG_PROVIDERS` с уникальным тегом
3. Обнови union-тип (например, `Updates = MessageCreated | BotStarted | ...`)

**Warming up retort**

`src/maxo/bot/warming_up.py` предзагружает все типы в retort при создании
бота, чтобы первый запрос не тратил время на генерацию сериализаторов. Adaptix
генерирует код на лету - warming_up делает это заранее.

**Различие `Omitted()` vs `None`**

- `Omitted()` - не отправлять поле в JSON
- `None` - отправить `{"field": null}`
- `Omittable[T] = Omitted()` для optional query/body параметров
- `Omittable[T | None]` для полей, которые могут быть `null`

### Observer Pattern и роутинг

**Иерархия фильтров**

В routing есть несколько уровней фильтров:

1. Фильтр на уровне observer'а (применяется ко всем handler'ам)
2. Фильтр на уровне каждого handler'а
3. Outer middleware (до фильтров)
4. Inner middleware (после фильтров, перед handler'ом)

**UNHANDLED vs SkipHandler**

- `UNHANDLED` - возвращается, если ни один handler не подошел. Update
  передается дочерним роутерам через `Router.include()`.
- `SkipHandler` (exception) - пропускает текущий handler, но продолжает искать
  следующий handler в том же observer'е. Update не идет к дочерним роутерам.

**Observer State Pattern**

После вызова startup-сигналов observer переходит в состояние, запрещающее
добавление новых handler'ов и фильтров. Это защита от изменения роутинга во
время работы бота.

**Алиасы для aiogram-совместимости**

```python
router.message = router.message_created  # алиас
router.callback_query = router.message_callback  # алиас
```

Используй явные имена (`message_created`) в новом коде. Алиасы нужны для
миграции с aiogram.

### Исключения, алиасы и канонические импорты

- Канонические update-типы находятся в `maxo.types`.
- Общие и API-исключения находятся в `maxo.errors`, dialog-исключения - в
  `maxo.dialogs.api.exceptions`, а управляющие исключения routing - в
  `maxo.routing.sentinels`.

**Конфликт метаклассов: фасады не могут быть ABC**

`BaseMethodsFacade` (`src/maxo/types/facades/base.py`) - корень цепочки фасадов и
одновременно подмешан в `MaxoType`. Наследоваться от `ABC`/`Protocol` он не
может: `_MaxoTypeMetaClass` конфликтует с `ABCMeta`. Поэтому `@abstractmethod`
на фасадах декоративный, а поля вроде `message` объявлены раздвоённо через
`if TYPE_CHECKING`.

Это технический долг. `MaxoType` наследует `BaseMethodsFacade` временно -
когда наследование уберут, фасады станут настоящими ABC. Не пытайся
использовать ABC с MaxoType сейчас - будут ошибки инициализации.

### Bot API и unihttp

**Marker-based declarative API**

Bot API методы используют marker-типы для декларативного указания, куда идут
параметры:

```python
class SendMessage(MaxoMethod[SendMessageResult]):
    __url__ = "messages"
    __method__ = "post"

    chat_id: Query[Omittable[int]] = Omitted()  # -> query string
    text: Body[str | None] = None  # -> JSON body
```

`bind_method` из `unihttp` анализирует маркеры и автоматически создает метод:

```python
send_message = bind_method(SendMessage)  # в Bot классе
```

**Generic-параметр = тип результата**

`MaxoMethod[SendMessageResult]` указывает, что метод вернет
`SendMessageResult` после десериализации ответа API.

**Патчинг success=false**

`src/maxo/bot/api_client.py` содержит специальную логику:

```python
if response.ok and response.data.get("success", None) is False:
    if isinstance(method, AddMembers):
        return  # Особый случай
    response.status_code = 400
```

MAX API иногда возвращает HTTP 200 с `"success": false`. Для большинства
методов это патчится на 400, но для `AddMembers` остается как есть, т.к. там
детальная информация в результате.

### FSM и изоляция

**DefaultKeyBuilder с destiny**

Для dialogs **обязательно** использовать `DefaultKeyBuilder(with_destiny=True)`:

```python
# Правильно для dialogs
isolation = SimpleEventIsolation(DefaultKeyBuilder(with_destiny=True))

# Неправильно - будут коллизии ключей в multiple stacks
isolation = SimpleEventIsolation(DefaultKeyBuilder())
```

`destiny` - дополнительный параметр для изоляции стейта. Dialogs используют
его для работы с несколькими стеками диалогов одновременно.

**Ключи FSM формата: `{bot_id}:{chat_id}:{user_id}:{destiny}`**

При `with_destiny=False` попытка использовать `destiny != "default"` вызовет
`ValueError` - это защита от случайных коллизий.

### Dialogs и widgets

**Dialog наследует Router, но запрещает include()**

```python
class Dialog(Router, DialogProtocol):
    def include(self, *routers: BaseRouter) -> None:
        raise TypeError("Dialog cannot include routers")
```

Dialog использует observers от Router, но управляет ими самостоятельно. У
диалога автоматически настраиваются фильтры через `IntentFilter` для
перехвата только своих update'ов.

**Intent ID в callback payload**

Когда widget создает callback button, в payload добавляется intent_id:

```python
payload = f"{intent_id}:{widget_id}:{data}"
```

При обработке callback intent_id извлекается и используется для загрузки
правильного контекста. Это позволяет работать с multiple stacks - одна кнопка
может открывать диалог в новом стеке.

**ManagedWidget pattern**

`manager.find(widget_id)` возвращает `ManagedWidget`, а не сам виджет:

```python
class ManagedWidget(Generic[W]):
    def __init__(self, widget: W, manager: DialogManager):
        self.widget = widget
        self.manager = manager

    def __getattr__(self, item: str):
        return getattr(self.widget, item)  # проксирует атрибуты
```

Это позволяет виджету иметь доступ к `manager` без явной передачи. Виджеты
определяют метод `managed(self, manager)` для создания специфичного
managed-варианта с дополнительными методами.

**Stack ограничен 100 вложенными диалогами**

`src/maxo/dialogs/api/entities/stack.py` защищает от бесконечной рекурсии.
Если попытаться открыть 101-й диалог в одном стеке, будет ошибка.

**ID генерация на основе timestamp + random**

```python
def new_int_id() -> int:
    return int(time.time() * 1000) % 100_000_000 + random.randint(0, 99) * 100_000_000
```

ID конвертируются в короткую base62-подобную строку для использования в
callback payload. Это позволяет уместить ID в ограничения MAX API на длину
payload.

**Известное ограничение:** ID могут совпасть, если диалоги запущены в одну
миллисекунду. Формат сохранен ради короткого callback payload; не добавляй
локальные обходы коллизии без отдельного изменения публичного контракта.

### Webhook и collect_used_updates

**Подписка только на используемые update'ы**

MAX API требует явную подписку на типы update'ов для webhook.
`collect_used_updates(dispatcher)` рекурсивно обходит все роутеры и собирает
типы update'ов, на которые есть handlers:

```python
used_types = collect_used_updates(dp)
# Результат: [UpdateType.MESSAGE_CREATED, UpdateType.MESSAGE_CALLBACK, ...]
```

Это оптимизация - webhook не получает лишние update'ы, на которые нет
handlers.

### Частые ошибки и gotchas

**❌ Нельзя**: Использовать ABC с MaxoType

```python
# Ошибка - конфликт метаклассов
class MyType(MaxoType, ABC):
    pass
```

**❌ Нельзя**: Добавлять handlers после startup

```python
async def startup():
    router.message_created(handler)  # TypeError - observer в финальном состоянии
```

**❌ Нельзя**: Использовать dialogs без `with_destiny=True`

```python
# Будут коллизии ключей FSM
isolation = SimpleEventIsolation(DefaultKeyBuilder())  # неправильно для dialogs
setup_dialogs(dp, events_isolation=isolation)
```

**❌ Нельзя**: Вручную редактировать сгенерированные типы без синхронизации

При изменении контракта Bot API нужно синхронизировать: методы, типы, enum,
сериализацию, тесты, документацию.

**❌ Нельзя**: Путать `Omitted()` и `None`

```python
# Разное поведение:
SendMessage(text=Omitted())  # поле не отправляется
SendMessage(text=None)  # отправляется {"text": null}
```

**✅ Можно**: Вызывать методы на update'ах после привязки бота

```python
message = update.message.as_(bot)
await message.send_message(text="Reply")  # работает через BaseMethodsFacade
```

**✅ Можно**: Использовать `unsafe_*` для гарантированно присутствующих полей

```python
# Если уверен, что sender есть:
user = message.unsafe_sender  # User, не Omittable[User]
```

**✅ Можно**: Расширять TAG_PROVIDERS для новых полиморфных типов

```python
# В serialization.py добавь:
TAG_PROVIDERS = concat_provider(
    existing_providers,
    has_tag_provider(MyNewType, "type", MyEnum.VALUE),
)
```

## Публичный API

- Top-level `maxo` экспортирует только самые частые объекты:
  `Bot`, `Dispatcher`, `Router`, `Ctx`, `BaseMiddleware`, `__version__`,
  хелперы разметки `html` и `md`, а также модули `enums`, `methods`, `types`.
  Набор повторяет корень `aiogram`, чтобы упростить портирование ботов.
- Не расширяй top-level `maxo` без причины. Менее частые объекты должны
  импортироваться из своих публичных модулей.
- `maxo.methods` - тонкий реэкспорт `maxo.bot.methods` с явным списком имен.
  При добавлении метода Bot API обнови оба `__all__`; расхождение ловит
  `tests/maxo/test_public_api.py`.
- `maxo.exceptions` и `maxo.filters` - постоянные алиасы `maxo.errors` и
  `maxo.routing.filters` для портирования ботов с `aiogram`. Они не
  предупреждают при импорте и не планируются к удалению. Не путай их с
  переездами внутри пакета (`maxo.utils.long_polling` ->
  `maxo.transport.long_polling`) - те кидают `DeprecationWarning` и будут
  удалены.
- Документация и примеры должны импортировать из публичных модулей, а не из
  `maxo._internal`.
- При добавлении публичного символа обновляй ближайший `__init__.py` и
  `__all__`, если модуль использует явный публичный экспорт.

## Главные правила разработки

- Пиши инструкции для ИИ, docstrings публичного API и пользовательскую
  документацию на русском языке.
- Используй только короткое тире `-`. Не добавляй другие Unicode-варианты тире.
- Не используй `from __future__ import annotations` в новых файлах.
- Не добавляй `Co-Authored-By` в коммиты и текст PR.
- Коммиты оформляй в стиле conventional commits, например `feat:`, `fix:`,
  `docs:`, `chore:`. Русский текст в сообщении допустим.
- Строки держи до 88 символов, используй двойные кавычки и отступ 4 пробела.
- Строгая типизация обязательна: `mypy` работает в `strict = true` для
  `src/maxo`, `tests` и `examples`.
- Публичный код должен быть полностью аннотирован. В тестах аннотации тоже
  проверяются `mypy`, хотя ruff-правила `ANN` для тестов отключены.
- Не добавляй `Any`, `cast`, `type: ignore` и отключение lint-правил без
  локального объяснения причины.
- В `cast` передавай тип как есть, а не строкой: `cast(Retort, x)`, а не
  `cast("Retort", x)`. Если тип импортирован только под `TYPE_CHECKING` и в
  рантайме недоступен, тогда передавай его как строку.
- Если `type: ignore` неизбежен, указывай конкретный код ошибки.
- Для внутренних путей используй `pathlib.Path`, если работа идет с файлами.
- Не добавляй top-level side effects, кроме декларативной регистрации,
  ожидаемой текущими API.
- Не прячь импорты внутрь функций без необходимости. Предпочитай обычные
  импорты на уровне модуля.
- Для новых data-моделей используй существующий стиль: `MaxoType` для
  API-моделей, `@dataclass(slots=True)` там, где в подсистеме уже принят
  dataclass-подход.
- Не добавляй сетевые вызовы, чтение env-переменных, запуск процессов и
  работу с файловой системой при импорте модулей.
- Не коммить локальные артефакты: `__pycache__`, `.DS_Store`, `.pytest_cache`,
  `.ruff_cache`, `.mypy_cache`, `coverage.xml`, `htmlcov/`, `docs/_build/`.
- Не редактируй сгенерированные типы, enum и методы Bot API вручную как
  изолированную правку. Если меняется контракт API, синхронизируй методы,
  типы, сериализацию, тесты и документацию.

## FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию. Без явных настроек используются
  `MemoryStorage`, `SimpleEventIsolation`, `DefaultKeyBuilder`.
- Для production и нескольких процессов используй Redis storage/isolation и
  продуманную стратегию ключей.
- `maxo.dialogs` живет поверх FSM и добавляет свои observers/middlewares через
  `setup_dialogs(dp)`.
- `setup_dialogs` должен применяться к `Dispatcher` после подключения диалогов
  к роутеру.
- Для dialogs нужна изоляция с `DefaultKeyBuilder(with_destiny=True)`. В
  `setup_dialogs` это используется по умолчанию для dialog event isolation, но
  при кастомной FSM-конфигурации проверяй совместимость ключей.
- Все widget `id` внутри одного окна/диалога должны быть стабильными и
  уникальными.

## Bot API, `unihttp`, `adaptix`

- Методы Bot API - классы `MaxoMethod[Result]` с `__url__`, `__method__` и
  marker-полями из `maxo.bot.methods.markers`.
- Path, query, header и body должны соответствовать wire-контракту MAX Bot API.
- Generic-параметр `MaxoMethod[Result]` - тип результата после deserialization.
- `Bot` привязывает методы через `unihttp.bind_method`. Не пиши ручные
  passthrough-методы, если достаточно `bind_method`.
- Различай `Omitted()` и `None`: `Omitted()` значит "не отправлять поле",
  `None` значит отправить `null`, если это поддерживает API.
- Для optional wire-полей используй `Omittable[T] = Omitted()`.
- Для поля, которое может прийти как `null`, используй `Omittable[T | None]`.
- Для unsafe-доступа к omitted/null полям следуй паттернам `unsafe_sender`,
  `unsafe_url` и `AttributeIsEmptyError`.
- Полиморфные типы update, attachments, markup и buttons регистрируются в
  `src/maxo/serialization.py` через `TAG_PROVIDERS`. При добавлении нового
  варианта обнови retort.
- `serialization.py` также отвечает за query dumping, defaults из
  `BotDefaults`, attachments `to_request()`, timestamps в `datetime` с `UTC` и
  привязку `Bot` через `create_retort_with_bot`.
- `MaxApiClient` добавляет российский trusted CA, `Authorization`, `User-Agent`,
  обработку ошибок API и patch для `success=false`. Не ломай эти гарантии.
- Особый случай `AddMembers` в обработке `success=false` не меняй без
  отдельного теста и обновления документации.
- `Bot.download` принимает URL или `AttachmentPayload`; сохраняет в файл или
  возвращает `BinaryIO`.
- Если меняется контракт MAX Bot API, синхронизируй метод, типы, enum,
  update-модель, facade/mixin при пользовательском удобстве, сериализацию,
  тесты и документацию.

## Кодогенерация: butcher

`src/maxo/types`, `src/maxo/enums` и `src/maxo/bot/methods` генерируются из
`max-swagger.json` в корне - это единственный источник правды по контракту API.
Генератор живёт в `butcher/` и работает поверх PyPI-пакета
`unihttp-openapi-generator==0.3.1` из dependency group `butcher`. Запуск -
`just butcher`.

**Правила генерации - в `butcher/AGENTS.md`.** Читай его перед любой правкой
`butcher/`, перед синхронизацией со свагером и когда нужно понять, почему
сгенерированный файл выглядит именно так.

## Зависимости и optional extras

- Runtime-зависимости задаются в `pyproject.toml`; не добавляй новые
  зависимости без необходимости и проверки минимальных версий.
- Optional extras: `maxo[magic_filter]`, `maxo[dishka]`, `maxo[redis]`,
  `maxo[fastapi]`, `maxo[preview]`.
- Dev-группа подтягивает lint, tests, docs и основные extras. Для разработки
  используй `uv sync --all-groups`, чтобы тесты optional-интеграций не падали
  из-за отсутствующих зависимостей.
- Для новых optional-интеграций обновляй `pyproject.toml`, документацию,
  примеры и тесты импорта/поведения без обязательного внешнего сервиса.

## Тесты

### Общие правила

- Используй `pytest`, `pytest-asyncio` в `auto` mode и `unittest.mock`.
- Для async-кода тесты тоже async. Не запускай event loop вручную без причины.
- Новая функциональность требует узких тестов рядом с соответствующей
  подсистемой: `tests/maxo`, `tests/maxo_dialog`, `tests/maxo_webhook`.
- Для `maxo.dialogs` предпочитай test tools из `src/maxo/dialogs/test_tools`:
  `BotClient`, `MockMessageManager`, memory storage и локаторы клавиатуры.
- Для webhook используй существующие fixtures в `tests/maxo_webhook`.
- Не добавляй тесты, которые требуют реального MAX API или сетевого доступа.
- Тест должен фиксировать поведение, а не внутреннюю реализацию, если только
  задача не касается внутреннего контракта.
- Цель проекта - покрытие тестами на уровне 90%+. Текущее покрытие смотри через
  `uv run pytest tests/ --cov=src --cov-report=term`.

### Структура тестов и conftest.py

Тесты организованы по подсистемам в зеркальной структуре к `src/`:

```text
tests/
├── maxo/              # тесты для src/maxo (routing, fsm, bot)
├── maxo_dialog/       # тесты для src/maxo/dialogs
│   └── widgets/
│       ├── conftest.py          # фикстура mock_manager
│       ├── input/
│       │   ├── conftest.py      # хелперы для input-виджетов
│       │   ├── test_text.py
│       │   ├── test_combined.py
│       │   └── test_base.py
│       └── kbd/
└── maxo_webhook/      # тесты для src/maxo/transport/webhook
```

**Правила использования conftest.py:**

- Создавай `conftest.py` рядом с группой связанных тестов для shared fixtures
- Выноси дублирующиеся хелперы (создание сообщений, моков) в ближайший conftest
- Не дублируй код между тестовыми файлами - используй относительные импорты
  из conftest: `from .conftest import create_text_message`
- Каждая директория с тестами должна иметь `__init__.py` (требование ruff INP001)

### Хелперы для тестирования dialogs

**Фикстура mock_manager** (`tests/maxo_dialog/widgets/conftest.py`):

```python
@pytest.fixture
def mock_manager() -> DialogManager:
    manager = MagicMock()
    context = Context(
        dialog_data={},
        start_data={},
        widget_data={},
        state=State(),
        _stack_id="_stack_id",
        _intent_id="_intent_id",
    )
    manager.current_context = Mock(side_effect=lambda: context)
    manager.is_preview = MagicMock(return_value=False)
    return manager
```

**Хелперы для создания сообщений** (`tests/maxo_dialog/widgets/input/conftest.py`):

```python
def create_text_message(text: str) -> MessageCreated:
    """Создает текстовое сообщение для тестов."""
    return MessageCreated(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        message=Message(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=text),
        ),
    )

def create_photo_message() -> MessageCreated:
    """Создает сообщение с фото-вложением."""
    photo = PhotoAttachment(
        type=AttachmentType.IMAGE,
        payload=PhotoAttachmentPayload(
            photo_id=123,
            token="test_token",  # noqa: S106
            url="https://example.com/photo.jpg",
        ),
    )
    return MessageCreated(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        message=Message(
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            body=MessageBody(mid="test_mid", seq=1, text=None, attachments=[photo]),
        ),
    )

def setup_mock_manager(
    mock_manager: DialogManager,
    event: MessageCreated | None = None,
) -> None:
    """Настраивает mock_manager для работы с фильтрами."""
    mock_manager.middleware_data = {"ctx": {}}
    if event:
        mock_manager.event = event
```

### Паттерны тестирования widgets

**Базовый тест widget:**

```python
async def test_text_input_basic(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input = TextInput(id="text", on_success=on_success)

    message = create_text_message("Hello World")
    result = await text_input.process_message(message, None, mock_manager)

    assert result is True
    on_success.assert_called_once()
    assert text_input.get_value(mock_manager) == "Hello World"
```

**Тестирование с type factory:**

```python
async def test_text_input_with_type_factory(mock_manager: DialogManager) -> None:
    on_success = AsyncMock()
    text_input = TextInput(id="number", type_factory=int, on_success=on_success)

    message = create_text_message("42")
    result = await text_input.process_message(message, None, mock_manager)

    assert result is True
    call_args = on_success.call_args
    assert call_args[0][3] == 42  # data parameter (converted value)
```

**Тестирование фильтров:**

```python
async def test_message_input_with_content_type(
    mock_manager: DialogManager,
) -> None:
    message = create_photo_message()
    setup_mock_manager(mock_manager, message)  # важно: передать event

    handler = AsyncMock()
    message_input = MessageInput(
        func=handler,
        content_types=AttachmentType.PHOTO,
        id="input",
    )

    result = await message_input.process_message(message, None, mock_manager)

    assert result is True
    handler.assert_called_once()
```

**Тестирование managed widgets:**

```python
async def test_counter_managed(mock_manager: DialogManager) -> None:
    counter = Counter(id="counter")
    await counter.set_value(mock_manager, 5)

    managed = counter.managed(mock_manager)
    assert managed.get_value() == 5
```

### Edge cases для dialogs

Всегда тестируй:

- Пустые сообщения (`create_text_message("")`)
- Сообщения без body (`body=None`)
- Фильтры, возвращающие `False`
- Обработчики ошибок (`on_error` callbacks)
- Граничные значения для pagination (`page=0`, `page > max`)
- Пустые списки items в `ListGroup`

### Тестирование с AsyncMock

Для async callbacks используй `AsyncMock`:

```python
on_success = AsyncMock()
on_error = AsyncMock()
filter_func = AsyncMock(return_value=True)

# Проверка вызовов
on_success.assert_called_once()
on_success.assert_not_called()
assert filter_func.call_count == 2

# Проверка аргументов
call_args = on_success.call_args
assert call_args[0][3] == expected_value  # позиционный аргумент
```

### Coverage и работа с непокрытым кодом

Проверка текущего покрытия:

```bash
uv run pytest tests/ --cov=src --cov-report=term
uv run pytest tests/ --cov=src --cov-report=html  # для детального отчета
```

При добавлении тестов для увеличения покрытия:

1. Найди файлы с низким покрытием в coverage report
2. Изучи непокрытые строки (coverage.xml или htmlcov/)
3. Посмотри на существующие тесты в aiogram_dialog submodule для паттернов
4. Создай тесты, покрывающие happy path и edge cases
5. Используй shared helpers из conftest.py
6. Проверь, что новые тесты увеличили покрытие

### Специфичные проверки для подсистем

**Для Bot API и сериализации:**

- Request markers, dump defaults, `Omitted()`, `None`
- Загрузка ответа/update
- Polymorphic dispatch
- Маппинг ошибок API

**Для routing:**

- Порядок обработки `Router.include`
- Observers, middlewares
- `UNHANDLED`, `SkipHandler`

**Для FSM:**

- State transitions
- Data persistence
- Key builder
- Event isolation

**Для dialogs:**

- Старт, закрытие, переходы между окнами
- Callback widgets
- Dialog data
- Фоновые менеджеры
- Стабильность widget `id`

**Для webhook:**

- Положительный и отрицательный сценарии проверки секрета
- Routing и adapter mapping
- Mock/stub транспорта

### Рефакторинг тестов

При обнаружении дублирования:

1. Создай `conftest.py` в директории с тестами
2. Вынеси общие хелперы (create_*, setup_*)
3. Обнови импорты в тестах: `from .conftest import helper_name`
4. Убедись, что все тесты проходят после рефакторинга
5. Запусти `uv run ruff check --fix tests/` для проверки стиля

## Документация и примеры

- Документация находится в `docs/` и собирается Sphinx. Основной формат страниц
  - `rst`, changelog - `docs/pages/changelog.md`.
- Новые пользовательские возможности требуют обновления docs и, если уместно,
  `examples/`.
- Примеры должны импортировать только публичный API и быть совместимыми с
  текущей версией `0.8.0`.
- При изменении структуры docs обновляй `docs/index.rst` и соответствующие
  `toctree`.
- В README держи короткие актуальные примеры. Детальные объяснения отправляй в
  `docs/pages/...`.
- Все пользовательские инструкции и примеры для ИИ в этом репозитории пиши на
  русском языке.
- В новых docs чаще используй явные observers `message_created` и
  `message_callback`; алиасы `message`, `callback_query`, `edited_message`
  упоминай как совместимость.
- Клавиатуры показывай через `maxo.utils.builders.KeyboardBuilder`.
- `magic_filter` показывай через
  `maxo.integrations.magic_filter.MagicFilter`.
- Для webhook показывай `SimpleEngine`, `AiohttpWebAdapter` или
  `FastApiWebAdapter`, `StaticRouting`, `Security`, `StaticSecretToken`,
  `collect_used_updates`.
- Локальная сборка документации:

```bash
uv run sphinx-build -b html docs docs/_build/html
```

- При изменении docs не коммить `docs/_build/`; это локальный build output.
- При изменении `docs/conf.py`, `_static`, `_extra/llms.txt` или sitemap
  проверяй, что сборка Sphinx проходит.

## CI и качество

- `.github/workflows/lint.yml` запускает Python `3.14`, установку через
  `uv sync --all-groups`, затем отдельными шагами через `uv run`:
  `ruff check --no-fix .`, `mypy --config-file pyproject.toml`,
  `codespell src examples`, `slotscheck -m maxo`, `bandit -c pyproject.toml src -r`.
- `.github/workflows/test.yml` запускает Python `3.12`, `3.13`, `3.14` с
  dependency resolution `lowest-direct` и `highest`, затем
  `just test --cov-report=xml`. Матрицу версий гоняет сам GitHub Actions,
  поэтому `just test-all` (nox) в CI не используется.
- `.github/workflows/relator.yml` отправляет уведомления о новых issues и PR в
  Telegram через закрепленный action `reagento/relator`.
- `just lint` запускает `codespell`, `slotscheck` и `bandit` наравне с `ruff`.
  Учитывай их при изменении пользовательского текста, `__slots__`,
  dataclass-моделей и security-sensitive кода.
- `black` есть в lint-группе, но форматирование проекта задает `ruff format`.
  Не переформатируй весь репозиторий без отдельной задачи.

## Что важно помнить о текущем проекте

- Проект на `uv`, не на `pip` как основном инструменте для разработки.
- Используются `justfile` для локальных команд.
- `pyproject.toml` содержит строгие правила `ruff` и `mypy`.
- `src/maxo/types/` и `src/maxo/enums/` содержат много файлов, которые
  фактически являются generated API surface. Генерирует их `just butcher` -
  правила в `butcher/AGENTS.md`.
- `src/maxo/bot/methods/` тоже относится к API surface и требует синхронизации
  с типами, enum и сериализацией.
- Движок кодогенерации `unihttp-openapi-generator==0.3.1` устанавливается из
  PyPI через dependency group `butcher`.
- `maxo.dialogs` и `maxo.transport.webhook` исторически портированы из
  `aiogram_dialog` и `aiogram-webhook`, поэтому рядом с изменениями нужно
  проверять совместимость паттернов.
- Для hook- и transport-изменений обязательно смотреть на тесты в
  `tests/maxo_webhook`.
- `.agents/skills` и `.claude/skills` не используются как источник правил.
  Обязательные инструкции держи в `AGENTS.md` или во вложенных `AGENTS.md`.

## Перед PR

- Проверь рабочее дерево и не перезаписывай чужие изменения.
- Добавь тесты к измененному поведению.
- Обнови docs/examples при изменении пользовательского API.
- Если меняешь команды разработки, обновляй `justfile`,
  `AGENTS.md` и при необходимости CI workflows вместе.
- В PR-шаблоне честно отметь использование ИИ: код может быть написан ИИ, но
  должен пройти полный контроль человека.
- Не добавляй `Co-Authored-By`.
- Сообщения коммитов могут быть на русском, но должны оставаться понятными и
  следовать conventional commits.

## Перед завершением задачи

Минимальный чеклист:

- Код соответствует текущим паттернам соседних файлов.
- Публичный API, docs и examples синхронизированы.
- Добавлены или обновлены тесты для измененного поведения.
- Запущены релевантные проверки. Если проверка не запускалась, явно укажи
  причину.
- Не перезаписаны чужие изменения в рабочем дереве.
