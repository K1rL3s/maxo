# AGENTS.md - правила разработки maxo для AI-агентов

`maxo` - асинхронный Python-фреймворк для ботов мессенджера MAX
(`https://max.ru`), по API близкий к `aiogram`. Версии проекта и Python - в
`pyproject.toml`.

Инструкции для агентов, docstring'и публичного API и пользовательская
документация - на русском.

## Источник инструкций

`AGENTS.md` - единственный обязательный источник правил для всех агентов;
`CLAUDE.md` рядом - симлинк на него. Правила для Codex, Cursor, Copilot и
Gemini держи здесь, не в Claude-only skills; файлы под отдельный инструмент -
тонкий слой поверх. Исключение -
`.agents/skills/butcher-update/references/manual-layer.md`: общий справочник
ручного слоя, на него ссылается `butcher/AGENTS.md`.

Разросшуюся область выноси во вложенный `AGENTS.md` (так сделано для
`butcher/`) с симлинком `CLAUDE.md`. Он дополняет корневой.

## Команды

Проект на `uv`, команды в `justfile` (рецепты сами зовут `uv run`).

```bash
uv sync --all-groups   # все extras, иначе падают тесты интеграций
just lint              # ruff + black + codespell + slotscheck + bandit
just mypy
just test              # аргументы pytest: just test -k dialogs
uv run pytest tests/path/test_file.py::test_name -v
```

- `ruff` с `fix = true`, рецепты `just ruff`/`just black` правят файлы. Проверка
  без правок: `uv run ruff check --no-fix .`, `uv run black --check .`. Поэтому
  `lint.yml` зовёт линтеры через `uv run`, не `just`: иначе CI чинил бы найденное
  и зеленел.
- `uv.lock` в `.gitignore`; не коммить без решения мейнтейнера.
- Версия `uv` закреплена в четырёх местах, меняй все: `[tool.uv]
  required-version` (источник правды), `build-system.requires` (`uv_build`),
  вход `version` у `astral-sh/setup-uv` в каждом workflow, `pip install uv==...`
  в `.readthedocs.yml` (без пина RTD поставит свежий, сборка docs упадёт).

## Карта пакета

| Путь                        | Что там                                                          |
|-----------------------------|------------------------------------------------------------------|
| `src/maxo/bot/`             | `Bot`, `MaxApiClient`, методы Bot API на `unihttp`, `warming_up.py` |
| `src/maxo/types/`, `enums/` | Типы и enum MAX Bot API, в основном сгенерированы butcher        |
| `src/maxo/routing/`         | `Dispatcher`, `Router`, observers, filters, middlewares, signals, flags |
| `src/maxo/fsm/`             | `State`, `StatesGroup`, `FSMContext`, storage, isolation, key builders |
| `src/maxo/dialogs/`         | Порт `aiogram_dialog`                                            |
| `src/maxo/transport/`       | Long polling и webhook (engines, adapters, routing, security)    |
| `src/maxo/errors/`          | Общие и API-исключения                                           |
| `src/maxo/integrations/`    | `dishka`, `magic_filter`                                         |
| `src/maxo/utils/`           | Builders, upload, formatting, deeplink/link                      |
| `butcher/`                  | Кодогенерация по свагеру, свой `AGENTS.md`                       |

`maxo.dialogs` и `maxo.transport.webhook` портированы из `aiogram_dialog` и
`aiogram-webhook`: держи совместимость их паттернов.

## Неочевидные механизмы

### Типы

- `_MaxoTypeMetaClass` (`types/base.py`) сам оборачивает каждого наследника
  `MaxoType` в `@dataclass(slots=True, kw_only=True)`. Явный `__slots__` в
  классе отключает это.
- `MaxoType` наследует `BaseMethodsFacade` (`types/facades/base.py`), метакласс
  конфликтует с `ABCMeta`: ни `MaxoType`, ни фасады не могут быть
  `ABC`/`Protocol`. Поэтому `@abstractmethod` на фасадах декоративный, а поля
  вроде `message` объявлены раздвоённо через `if TYPE_CHECKING`. Технический
  долг до отвязки `MaxoType` от фасада.
- `maxo/types/facades/__init__.py` пуст намеренно: реэкспорт фасадов зацикливает
  импорт через `types/base.py`. Импортируй из модуля:
  `from maxo.types.facades.chat import ChatMethodsFacade`.
- Loader из `serialization.py` привязывает `Bot` ко всем загруженным типам,
  поэтому update отвечает сам: `await message.send_message(...)`. Вручную -
  `as_(bot)`.
- `Omitted()` - поле не отправляется, `None` в теле - уходит `null`, `None` в
  `Query[...]` становится `Omitted()` (`_omit_none_query_values`). Optional
  wire-поле - `Omittable[T] = Omitted()`, приходящее `null` -
  `Omittable[T | None]`. Для каждого `Omittable`-поля есть `unsafe_<поле>`,
  кидающий `AttributeIsEmptyError` (образец - `unsafe_sender`).
- Полиморфные типы (updates, attachments, markup, buttons) регистрируются в
  `TAG_PROVIDERS` в `serialization.py`. Union-алиас генерируется, регистрация
  ручная; без неё `LoadError` в рантайме. Порядок - в `butcher/AGENTS.md`.
- `serialization.py` ещё дампит query (bool -> `"true"`/`"false"`, списки через
  запятую, `datetime` в миллисекунды), грузит таймстемпы в `datetime` с `UTC` и
  подставляет `BotDefaults` (`text_format`, `disable_link_preview`). Дефолты
  получают только методы из ручных алиасов `TypesWithFormat` и
  `TypesWithLinkPreview`: новый метод с `format`/`disable_link_preview`
  добавляй туда.
- `bot/warming_up.py` заранее строит сериализаторы adaptix от корней: методов
  (`_METHOD_ROOTS`), их результатов и `Updates`, вложенные типы подхватываются
  сами. Новый метод добавляй в `_METHOD_ROOTS`, это проверяет
  `tests/maxo/bot/test_warming_up.py`.

### Роутинг

```text
Long polling / webhook -> Dispatcher -> Router tree
  -> outer middleware -> filters -> inner middleware -> handler
```

- `Dispatcher` - корневой `Router`; `Router.include(...)` задаёт порядок обхода.
  Первый обработавший update останавливает поиск.
- Фильтры бывают на observer'е (для всех его handler'ов) и на handler'е.
- Фильтр пишет в копию `ctx`: записи попадают в общий `ctx`, только если
  фильтр прошёл (`_run_isolated` в `routing/filters/logic.py`).
- `UNHANDLED` - ни один handler не подошёл, update идёт в дочерние роутеры.
  `SkipHandler` - пропустить текущий handler и искать дальше в том же
  observer'е, к дочерним роутерам update не идёт.
- После startup-сигналов observers замораживаются: позже добавленные handler
  или фильтр дают ошибку.
- `before_startup`, `after_startup`, `before_shutdown`, `after_shutdown` -
  lifecycle hooks, не update.
- `message`, `callback_query`, `edited_message` - алиасы `message_created`,
  `message_callback`, `message_edited` для портирования с aiogram. В новом коде
  и docs - явные имена.
- Флаги-маркеры хендлеров - `maxo.routing.flags`, инстанс `flags` экспортирует
  `maxo`.
- Webhook подписывается только на используемые update:
  `collect_used_updates(dispatcher)` обходит роутеры динамически.
- Long polling в docs и examples запускай через `Dispatcher.run_polling` (свой
  event loop) или `Dispatcher.start_polling` (уже в async); `LongPolling` - только
  ради `backoff_config`.
- Поллинг не перехватывает `SIGINT`/`SIGTERM`, но глушит `KeyboardInterrupt`:
  остановкой управляет приложение. Перехват сигналов не добавляй без решения
  мейнтейнера.

### Bot API

- Метод - класс `MaxoMethod[Result]` с `__url__`, `__method__` и маркерами
  полей из `maxo.bot.methods.markers` (`Path`, `Query`, `Header`, `Body`,
  `Form`, `File`), совпадающими с wire-контрактом. `Result` - тип ответа после
  десериализации.
- `Bot` привязывает методы через `unihttp.bind_method`; ручные
  passthrough-методы не пиши.
- Убранный или неподдерживаемый MAX метод помечается `@deprecated(...,
  stacklevel=2)` из `typing_extensions` на классе. `bind_method` создаёт
  экземпляр метода при каждом вызове, поэтому `DeprecationWarning` срабатывает и
  на `bot.<метод>()`, а `stacklevel=2` указывает на строку пользователя. mypy и
  IDE подсвечивают только импорт класса, не вызов через `Bot`. Сгенерированному
  методу пометку ставит butcher (`DEPRECATED_METHODS`). Импорты устаревших
  символов внутри maxo и в тестах - с `# type: ignore[deprecated]` (в mypy
  включён код `deprecated`).
- `MaxApiClient` добавляет российский trusted CA, `User-Agent` и маппинг ошибок
  API. `Authorization` ставит `AuthMiddleware`, только в запросы к API по
  относительному пути: токен не уходит на upload-хосты и в `Bot.download`.
- HTTP 200 с `"success": false` или `error_code` превращает в
  `MaxBotBadRequestError` `MaxoMethod.validate_response`. Исключение -
  `AddMembers`: его `validate_response` пустой, метод отдаёт частичный
  результат; без отдельного теста и документации это поведение не меняй.
- Заголовки `X-Max-Client-Name`, `X-Max-Client-Version`, `X-Max-Client-Runtime`
  повторяют телеметрию официальных Go- и TS-клиентов
  (max-messenger/max-bot-api-client-go#173,
  max-messenger/max-bot-api-client-ts#321), в документации MAX их нет. Как и
  `User-Agent`, они не перезаписывают заголовки пользовательской
  `ClientSession`.
- `Bot.download` принимает URL или `AttachmentPayload` и пишет в файл либо
  возвращает `BinaryIO`.

### FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию: `MemoryStorage`,
  `SimpleEventIsolation`, `DefaultKeyBuilder`. Для нескольких процессов - Redis
  storage/isolation.
- Ключ FSM: `{bot_id}:{chat_id}:{user_id}:{destiny}`. Dialogs держат несколько
  стеков через `destiny`, им нужен `DefaultKeyBuilder(with_destiny=True)`; без
  него `destiny != "default"` даёт `ValueError`. `setup_dialogs` ставит такую
  изоляцию сам, при кастомной FSM проверяй совместимость ключей.
- `setup_dialogs(dp)` вызывай после подключения диалогов к роутерам.
- `Dialog` наследует `Router`, но `include()` кидает `TypeError`; свои update
  диалог ловит через `IntentFilter`.
- Callback payload виджета - `{intent_id}:{widget_id}:{data}`, по `intent_id`
  грузится контекст. Widget `id` в окне и диалоге стабильны и уникальны.
- `manager.find(widget_id)` возвращает `ManagedWidget`, проксирующий атрибуты
  виджета и знающий `manager`; виджет расширяет его через `managed(manager)`.
- Стек - не больше 100 диалогов (`_STACK_LIMIT`).
- `new_int_id()` (время в мс + random) кодируется в короткую строку ради лимита
  длины payload. ID двух диалогов в одну миллисекунду могут совпасть - известное
  ограничение: обход коллизии требует изменить публичный контракт.

## Публичный API

- Top-level `maxo` повторяет корень `aiogram`: `Bot`, `Dispatcher`, `Router`,
  `Ctx`, `BaseMiddleware`, `flags`, `html`, `md`, модули `enums`, `methods`,
  `types`, `__version__`. Не расширяй без причины, остальное импортируется из
  своих модулей.
- Канонические места: update-типы - `maxo.types`; общие и API-исключения -
  `maxo.errors`; dialog-исключения - `maxo.dialogs.api.exceptions`; управляющие
  исключения routing - `maxo.routing.sentinels`.
- `maxo.methods` реэкспортирует `maxo.bot.methods`; `maxo.exceptions` и
  `maxo.filters` - постоянные алиасы `maxo.errors` и `maxo.routing.filters` для
  портирования с aiogram, без предупреждений и планов удаления (в отличие от
  переездов внутри пакета, которые кидают `DeprecationWarning`). Новый символ
  добавляй в `__all__` обоих модулей пары; расхождение ловит
  `tests/maxo/test_public_api.py`.
- Новый публичный символ - в ближайший `__init__.py` и его `__all__`.
- Docs и examples импортируют из публичных модулей, не из `maxo._internal`.

## Правила кода

- Без `from __future__ import annotations` в новых файлах.
- Строки до 88 символов, двойные кавычки, отступ 4. `ruff format` и `black`
  работают одновременно, дерево - неподвижная точка обоих. Если разошлись на
  новом коде, перепиши код, не конфиги. Репозиторий без отдельной задачи не
  переформатируй.
- `mypy` `strict` для `src/maxo`, `tests`, `examples`; публичный код и тесты
  аннотированы полностью.
- `Any`, `cast`, `type: ignore` и отключение lint-правил - только с локальным
  объяснением причины; у `type: ignore` - конкретный код ошибки. В `cast` тип
  передаётся объектом (`cast(Retort, x)`), строкой - только если импортирован под
  `TYPE_CHECKING`.
- Импорты на уровне модуля. При импорте - никаких сети, env, процессов, ФС и
  прочих side effects, кроме декларативной регистрации.
- Пути - `pathlib.Path`.
- Новые модели: `MaxoType` для API, `@dataclass(slots=True)` там, где в
  подсистеме принят dataclass.
- `just lint` гоняет ещё `codespell`, `slotscheck`, `bandit`: учитывай их в
  пользовательском тексте, `__slots__`, dataclass-моделях и security-коде.

## Кодогенерация: butcher

`src/maxo/types`, `src/maxo/enums`, `src/maxo/bot/methods` генерируются из
`max-swagger.json` и `max-swagger.yaml` - источника правды по контракту MAX Bot
API. Изменение контракта синхронизирует метод, типы, enum, сериализацию,
фасады, тесты и docs; изолированные ручные правки сгенерированных файлов не
делай.

**Прочитай `butcher/AGENTS.md` перед правкой `butcher/`, сгенерированных файлов
или свагеров.** Скилл `.agents/skills/butcher-update` - обёртка над ним, его
`references/manual-layer.md` - перечень ручного слоя поверх генерации.

## Зависимости

- Runtime-зависимость - только по необходимости и с проверкой минимальной
  версии: CI тестирует и `lowest-direct`.
- Extras: `magic_filter`, `dishka`, `redis`, `fastapi`, `preview`. Новый extra -
  это `pyproject.toml`, docs, examples и тесты без внешнего сервиса.

## Тесты

- `pytest` с `asyncio_mode = auto`, моки из `unittest.mock` (`AsyncMock` для
  async). Тесты зеркалят подсистемы: `tests/maxo`, `tests/maxo_dialog`,
  `tests/maxo_webhook`.
- Без реального MAX API и сети. Тест фиксирует поведение, не реализацию.
- В каждой тестовой директории `__init__.py` (ruff `INP001`). Общие хелперы - в
  ближайший `conftest.py`, импорт `from .conftest import ...`.
- Готовые хелперы: `mock_manager` в `tests/maxo_dialog/widgets/conftest.py`,
  `create_text_message`/`create_photo_message`/`setup_mock_manager` в
  `tests/maxo_dialog/widgets/input/conftest.py`, `maxo.dialogs.test_tools`
  (`BotClient`, `MockMessageManager`, memory storage, локаторы клавиатуры),
  фикстуры `tests/maxo_webhook`. Фильтры виджетов читают `manager.event` -
  передай его в `setup_mock_manager`.
- Dialogs: проверяй края - пустой текст, сообщение без body, фильтр с `False`,
  `on_error`, `page=0` и `page > max`, пустой `ListGroup`.
- Hooks и transport сверяй с `tests/maxo_webhook`; секрет webhook тестируй в
  положительном и отрицательном сценарии.
- Покрытие 90%+: `uv run pytest tests/ --cov=src --cov-report=term`.

## Документация и примеры

- Sphinx в `docs/`, страницы `rst`, changelog - `docs/pages/changelog.md`. Новые
  страницы - в `docs/index.rst` и нужный `toctree`. `docs/_build/` не коммить.
- Новая пользовательская возможность - обновить docs и, если уместно,
  `examples/`. README - короткие примеры, подробности - в `docs/pages/`.
- В примерах: явные observers (`message_created`, `message_callback`), алиасы -
  только как совместимость; клавиатуры - `maxo.utils.builders.KeyboardBuilder`;
  magic filter - `maxo.integrations.magic_filter.MagicFilter`; webhook -
  `SimpleEngine`, `AiohttpWebAdapter`/`FastApiWebAdapter`, `StaticRouting`,
  `Security`, `StaticSecretToken`, `collect_used_updates`.
- После правок `docs/conf.py`, `_static`, `_extra/llms.txt` или sitemap:
  `uv run sphinx-build -b html docs docs/_build/html`.

## CI

- `lint.yml` (Python 3.14): `ruff check --no-fix`, `black --check`, `mypy`,
  `codespell src examples`, `slotscheck -m maxo`, `bandit -c pyproject.toml src
  -r`. `test.yml`: Python 3.12-3.14 x резолвинг `lowest-direct`/`highest`,
  `just test --cov-report=xml`; `just test-all` (nox) в CI не используется.
- Резолвинг в `test.yml` задаёт `UV_RESOLUTION` на уровне job, не `uv sync
  --resolution`: иначе `uv run` в рецептах перерезолвил бы до `highest` и
  `lowest-direct` тестировал бы свежие версии. Локально:
  `UV_RESOLUTION=lowest-direct just test`.
- Python ставит `setup-uv` входом `python-version`, `actions/setup-python` нет.
  Кэш `uv` не настраивается (дефолты хватает). В `test.yml` нужен
  `cache-suffix: ${{ matrix.dependency-resolution }}`, иначе шесть job делят одну
  запись кэша.
- `build.yml` собирает sdist и wheel, проверяет `twine check --strict` и
  `check_dist.py`; его же через `workflow_call` зовёт `publish.yml`, так что
  публикуется проверенный артефакт. `twine` закреплён в группе `dev` и зовётся
  через `uv run`, не `uvx`: версия проверяльщика не должна меняться сама.
- `check_dist.py` - единственный источник правды по содержимому дистрибутива
  (`py.typed`, `russiantrustedca.pem`, лицензии, отсутствие мусора,
  импортируемость из одного колеса). Его зовут CI и `just check-dist`; голая
  stdlib, запуск `uv run --no-project`. `twine check` этих отказов не ловит -
  скрипт не убирай.
- `publish.yml` публикует на PyPI по `release: published` через OIDC Trusted
  Publishing (environment `pypi`), сверяет версию артефакта с тегом и
  прикладывает дистрибутив к релизу. Токена PyPI в секретах нет и не должно быть.
  `workflow_dispatch` нет намеренно: он обходил бы сверку версии с тегом.
- `relator.yml` шлёт уведомления о новых issues и PR в Telegram.
- Сторонние actions закреплены по полному SHA с комментарием версии (`zizmor`,
  `unpinned-uses`); пины обновляет dependabot. Новый шаг - сразу с SHA,
  `actions/checkout` - с `persist-credentials: false`.
- Меняешь команды разработки - обновляй вместе `justfile`, `AGENTS.md` и
  workflows.

## Перед завершением задачи

- Чужие изменения не перезаписаны; локальные артефакты (`__pycache__`,
  `.DS_Store`, кэши линтеров, `coverage.xml`, `htmlcov/`, `docs/_build/`) не
  попали в коммит.
- Изменённое поведение покрыто тестами; публичный API, docs и examples
  синхронизированы.
- Релевантные проверки прогнаны; не запускавшиеся - с причиной.
- Коммиты - conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), русский
  допустим, без `Co-Authored-By`. В PR-шаблоне честно отмечено использование
  ИИ: код может писать ИИ, но полностью проверяет его человек.
