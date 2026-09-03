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
| `src/maxo/bot/`          | `Bot`, `default_client`, middlewares клиента, дефолты, warming up, declarative Bot API methods на `unihttp`.                      |
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

**Автопривязка бота через BotMixin**

`BotMixin` живёт в `src/maxo/types/binding.py` (не в `base.py`) и даёт
`as_(bot)`, проперти `bot` и сеттер. Его получают не все `MaxoType`, а те, у
кого он есть в базах: фасады и апдейты с записью в `CLASS_MIXINS`. Благодаря
этому работает `await message.answer(...)` вместо `bot.send_message(...)`.

Неочевидное про `bind_bot`:

- Loader'а в retort **нет**. `bind_bot` зовётся снаружи: в `Bot.call_method`
  над результатом, в `as_()` и в сеттере `bot`.
- Спускается не во все поля, а только в ведущие к `BotMixin`. Их считает
  `_bot_fields` (`@cache`) по хинтам на любой глубине.
- Обход без `seen`: граф типов ацикличен, это держит тест
  `test_type_graph_is_acyclic` (`tests/maxo/test_binding.py`). Заведёшь цикл в
  типах - обход зациклится, тест упадёт первым.

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

`src/maxo/serialization.py` держит теги полиморфных типов в словарях по
семействам (`_UPDATE_TAGS`, `_ATTACHMENT_TAGS`, `_MARKUP_TAGS`,
`_ATTACHMENT_REQUEST_TAGS`, `_BUTTON_TAGS`). `_TAG_GROUPS` связывает каждый
словарь с union-алиасом и полем тега, а `TAG_PROVIDERS` собирается из
`_TAG_GROUPS` автоматически - плоского списка `has_tag_provider(...)` больше
нет, дописывать туда нечего.

При добавлении нового варианта в union-тип (новый update, attachment, button):

1. Создай класс, наследующий базовый тип
2. Добавь запись в словарь тегов своего семейства
3. Обнови union-тип (например, `Updates = MessageCreated | BotStarted | ...`)

**Warming up retort**

`src/maxo/bot/warming_up.py` предзагружает корневые типы в общую retort, чтобы
первый запрос не тратил время на генерацию сериализаторов. Adaptix генерирует
код на лету - warming_up делает это заранее.

Retort одна на процесс (`get_retort()`, `@cache`) и от конфига не зависит:
дефолты накладывает `apply_defaults()` в `Bot.call_method`, бота проставляет
`bind_bot()` над результатом. Не заводи retort с ключом по `BotDefaults` или
по боту - это ломает и прогрев, и кеш адаптикса.

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

- Канонические update-типы находятся в `maxo.types`. Пакет
  `maxo.routing.updates` сохраняется только как устаревший слой совместимости.
- Общие и API-исключения находятся в `maxo.errors`, dialog-исключения - в
  `maxo.dialogs.api.exceptions`, а управляющие исключения routing - в
  `maxo.routing.sentinels`.

**Конфликт метаклассов: BaseMethodsFacade = BotMixin**

`src/maxo/types/facades/base.py` содержит комментарий-исповедь:

```python
# Фасад должен был наследоваться от ABC ради @abstractmethod, но MaxoType
# сделан через метакласс и конфликтует с ABC в моделях апдейтов. Плюс
# BotMixin требует __slots__, а двойное наследование ломается - поэтому
# BaseMethodsFacade, который определял только проперти `bot`, стал алиасом.
BaseMethodsFacade = BotMixin
```

Это технический долг. Не пытайся использовать ABC с MaxoType - будут ошибки
инициализации.

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

`MaxoMethod.validate_response` в `src/maxo/bot/methods/base.py`:

```python
def validate_response(self, response: HTTPResponse[Any]) -> None:
    # MAX иногда отвечает 200 с `success: false`/`error_code` в теле.
    if response.ok and isinstance(response.data, dict) and (
        response.data.get("error_code")
        or response.data.get("success", None) is False
    ):
        response.status_code = 400
```

MAX API иногда возвращает HTTP 200 с `"success": false`. Для большинства
методов это патчится на 400 (дальше `on_error` -> `raise_api_error`), но
`AddMembers` перекрывает `validate_response` пустым телом: там при
`success=false` приходит частичный результат.

**Стек клиентских middleware `Bot`**

`Bot.__init__` собирает `self.middleware` в фиксированном порядке, и порядок
здесь - контракт, а не деталь:

```python
self.middleware = [
    *middlewares,                        # пользовательские, снаружи всех
    AuthMiddleware(token),               # Authorization + User-Agent
    AttachmentNotReadyRetryMiddleware(...),  # ретрай `attachment.not.ready`
    NetworkErrorMiddleware(),            # unihttp-ошибки -> ошибки maxo
]
```

`NetworkErrorMiddleware` стоит последним, то есть ближе всего к транспорту:
всё, что снаружи, уже видит `MaxBotNetworkError`/`MaxBotTimeoutError`, а не
сырые исключения `unihttp`. `ChunkUploadRetryMiddleware` в этот список не
входит - он передаётся точечно через `Bot.call_method(middleware=...)` при
resumable-загрузке и ретраит 5xx и сетевые сбои на отдельном чанке.

Параметры ретраев и порогов живут в `UploadConfig` (`src/maxo/bot/upload.py`):
`method`, `resumable_threshold`, `chunk_size`, `chunk_retries`,
`not_ready_max_retries`, две `BackoffConfig` и `processing_*` (ожидание
обработки медиа на стороне MAX). Все инварианты проверяются в `__post_init__`.
Не зашивай задержки в middleware - добавляй поле в `UploadConfig`.

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
# Результат: (UpdateType.MESSAGE_CREATED, UpdateType.MESSAGE_CALLBACK, ...)
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
    router.message_created(handler)  # StateError: Can't add handler after startup
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
await message.send_message(text="Reply")  # работает через BotMixin
```

**✅ Можно**: Использовать `unsafe_*` для гарантированно присутствующих полей

```python
# Если уверен, что sender есть:
user = message.unsafe_sender  # User, не Omittable[User]
```

**✅ Можно**: Регистрировать новые полиморфные типы

```python
# В serialization.py допиши в словарь тегов своего семейства:
_ATTACHMENT_TAGS: Mapping[type, AttachmentType] = {
    # ...
    MyNewAttachment: AttachmentType.MY_NEW,
}
```

Сам `TAG_PROVIDERS` руками не трогай - он собирается из `_TAG_GROUPS`.

## Публичный API

- Top-level `maxo` экспортирует только самые частые объекты: `Bot`,
  `Dispatcher`, `Router`, `Ctx`, `BaseMiddleware`, `flags`, `__version__`,
  хелперы разметки `html` и `md`, модули `enums`, `methods`, `types`, а также
  точки входа в клиент и реторту - `default_client`, `build_ssl_context`,
  `BASE_URL`, `get_retort`, `warm_up`. Ядро набора повторяет корень `aiogram`,
  чтобы упростить портирование ботов.
- Не расширяй top-level `maxo` без причины. Менее частые объекты должны
  импортироваться из своих публичных модулей.
- `maxo.methods` - тонкий реэкспорт `maxo.bot.methods` с явным списком имен.
  При добавлении метода Bot API обнови оба `__all__`; расхождение ловит
  `tests/maxo/test_public_api.py`.
- `maxo.exceptions` и `maxo.filters` - постоянные алиасы `maxo.errors` и
  `maxo.routing.filters` для портирования ботов с `aiogram`. Они не
  предупреждают при импорте и не планируются к удалению. Не путай их с
  переездами внутри пакета (`maxo.routing.updates`, `maxo.utils.facades`,
  `maxo.utils.long_polling`) - те остаются с `DeprecationWarning`.
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
  `src/maxo/serialization.py` в словарях тегов (`_UPDATE_TAGS`,
  `_ATTACHMENT_TAGS`, ...), из которых собирается `TAG_PROVIDERS`. При
  добавлении нового варианта обнови нужный словарь.
- `serialization.py` также отвечает за query dumping (включая омит `None` -
  MAX не переваривает `null` в query), attachments `to_request()` и timestamps
  в `datetime` с `UTC`. Дефолты и привязка `Bot` живут снаружи retort:
  `apply_defaults()` и `bind_bot()`.
- `default_client()` в `src/maxo/bot/client.py` подкладывает российский trusted
  CA (`russiantrustedca.pem`) и retort как dumper/loader; `Authorization` и
  `User-Agent` ставит `AuthMiddleware`, а patch `success=false`/`error_code` на
  400 и подъём ошибок API живут в `MaxoMethod` (`bot/methods/base.py`).
  Не ломай эти гарантии.
- Особый случай `AddMembers` в обработке `success=false` не меняй без
  отдельного теста и обновления документации.
- Скачивание - три метода, все принимают URL или `AttachmentPayload`:
  `Bot.download()` отдаёт `bytes`, `Bot.download_to()` пишет в файл (открываем
  и закрываем его мы), `Bot.download_stream()` - асинхронный контекстный
  менеджер с чанками. Зеркалят `InputFile.read()`/`FSInputFile`/
  `InputFile.stream()` на стороне загрузки - не разводи их сигнатуры.
  Два правила, из которых это выросло:
  - Не возвращай `destination` одним union-аргументом: из него росли `seek`
    и флаш чужого буфера. Буфер вызывающего флашит и закрывает вызывающий.
  - `download_stream()` - контекстный менеджер, а не голый генератор:
    соединение наше, освобождать его при `break` должны мы, а не вызывающий
    через `aclosing`. Форма та же, что у `aiohttp` и `httpx`.
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
  `maxo[webhook]`, `maxo[fastapi]`, `maxo[preview]`. `fastapi` включает в себя
  `webhook`.
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

- `tests/maxo_dialog/widgets/conftest.py` - фикстура `mock_manager`:
  `MagicMock` с настоящим `Context` внутри `current_context()` и
  `is_preview() -> False`.
- `tests/maxo_dialog/widgets/input/conftest.py` - `create_text_message`,
  `create_photo_message`, `create_message_no_body`, `setup_mock_manager`,
  `dialog_protocol`.
- Время в тестах бери из `tests/constants.NOW`, а не из своего
  `datetime(...)` - иначе тесты расходятся по таймзонам и по значениям.

Копии этих хелперов в документации не держим: смотри сами файлы.

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
2. Изучи непокрытые строки (`coverage.xml` или `htmlcov/`)
3. Создай тесты на happy path и edge cases, переиспользуя хелперы из
   ближайшего `conftest.py`
4. Проверь, что новые тесты увеличили покрытие

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

Дублирующиеся хелперы (`create_*`, `setup_*`) выноси в ближайший
`conftest.py` и импортируй относительно: `from .conftest import helper_name`.

## Документация и примеры

- Документация находится в `docs/` и собирается Sphinx. Основной формат страниц
  - `rst`, changelog - `docs/pages/changelog.md`.
- Новые пользовательские возможности требуют обновления docs и, если уместно,
  `examples/`.
- Примеры должны импортировать только публичный API и быть совместимыми с
  текущей версией `0.8.1`.
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
- Для webhook показывай `SingleBotEngine`, `AiohttpAdapter` или
  `FastAPIAdapter`, `Route`, `Security`, `StaticSecret`, `collect_used_updates`
  (в `WebhookConfig(update_types=...)` для `engine.subscribe(...)`).
- Из корня пакета `maxo.transport.webhook` реэкспортируются только
  `SingleBotEngine`, `TokenEngine`, `Route`, `WebhookConfig` и `BotConfig`.
  Адаптеры в корень не вынесены - каждый берётся из своего модуля:
  `maxo.transport.webhook.web.aiohttp` и `maxo.transport.webhook.web.fastapi`.
  Всё, что тянет опциональную зависимость, реэкспорту не подлежит: модуль
  импортирует её сверху и вешает
  `e.add_note("* Please run \`pip install maxo[...]\`")` (как
  `fsm/storages/redis.py` и `integrations/magic_filter.py`).
- `Security` и `StaticSecret` живут в `maxo.transport.webhook.security` и в
  корень не вынесены. Промежуточные `engines/__init__.py`, `configs/__init__.py`
  и `web/__init__.py` публичной поверхностью не являются: `web/__init__` отдаёт
  только безфреймворковые `WebAdapter`, `WebHandler`, `WebRequest`, остальные
  два пустые. Не пиши в доках импорт через них.
- Эталон примеров - `examples/webhook_aiohttp.py` и
  `examples/webhook_fastapi.py`: они под `mypy`, поэтому не отстают от кода.
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
- `src/maxo/bot/methods/` и `src/maxo/routing/updates/` тоже относятся к API
  surface и требуют синхронизации с типами, enum и сериализацией.
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
