# AGENTS.md - правила разработки maxo для AI-агентов

`maxo` - асинхронный Python-фреймворк для ботов мессенджера MAX
(`https://max.ru`), по API и привычкам близкий к `aiogram`. Версия проекта и
поддерживаемые Python - в `pyproject.toml`.

Инструкции для агентов, docstring'и публичного API и пользовательская
документация пишутся на русском языке.

## Источник инструкций

`AGENTS.md` - единственный обязательный источник правил для всех агентов;
`CLAUDE.md` рядом с ним - симлинк `./AGENTS.md`. Правила, нужные Codex, Cursor,
Copilot и Gemini, держи здесь, а не в Claude-only skills. Файлы под отдельный
инструмент - только тонкий слой поверх `AGENTS.md`. Исключение -
`.agents/skills/butcher-update/references/manual-layer.md`: общий для всех
инструментов справочник ручного слоя, на него ссылается `butcher/AGENTS.md`.

Разросшуюся область выноси во вложенный `AGENTS.md` рядом с кодом (так сделано
для `butcher/AGENTS.md`) с симлинком `CLAUDE.md -> ./AGENTS.md`. Вложенный файл
дополняет корневой, общие правила действуют и в подкаталоге.

## Команды

Проект на `uv`, команды собраны в `justfile`; рецепты сами зовут `uv run`.

```bash
uv sync --all-groups   # окружение со всеми extras, иначе падают тесты интеграций
just lint              # ruff + black + codespell + slotscheck + bandit
just mypy
just test              # принимает аргументы pytest: just test -k dialogs
uv run pytest tests/path/test_file.py::test_name -v
```

- В `pyproject.toml` у `ruff` стоит `fix = true`, а рецепты `just ruff` и
  `just black` правят файлы. Для проверки без правок:
  `uv run ruff check --no-fix .` и `uv run black --check .`. По той же причине
  `lint.yml` зовёт линтеры через `uv run`, а не через `just`: иначе CI чинил бы
  найденное и зеленел.
- `uv.lock` в `.gitignore`; не коммить его без решения мейнтейнера.
- Версия `uv` закреплена в четырёх местах, меняй все сразу:
  `[tool.uv] required-version` (источник правды, другой `uv` откажется
  работать), `build-system.requires` (`uv_build`), вход `version` у
  `astral-sh/setup-uv` в каждом workflow и `pip install uv==...` в
  `.readthedocs.yml` (RTD ставит `uv` через `pip`, без пина приедет свежий и
  сборка документации упадёт).

## Карта пакета

| Путь                     | Что там                                                                     |
|--------------------------|-----------------------------------------------------------------------------|
| `src/maxo/bot/`          | `Bot`, `MaxApiClient`, методы Bot API на `unihttp`, `warming_up.py`.         |
| `src/maxo/types/`, `enums/` | Типы и enum MAX Bot API, в основном сгенерированы butcher.               |
| `src/maxo/routing/`      | `Dispatcher`, `Router`, observers, filters, middlewares, signals, flags.     |
| `src/maxo/fsm/`          | `State`, `StatesGroup`, `FSMContext`, storage, isolation, key builders.      |
| `src/maxo/dialogs/`      | Порт `aiogram_dialog`: `Dialog`, `Window`, widgets, managers, test tools.    |
| `src/maxo/transport/`    | Long polling и webhook (engines, adapters, routing, security).               |
| `src/maxo/errors/`       | Общие и API-исключения.                                                     |
| `src/maxo/integrations/` | `dishka`, `magic_filter`.                                                   |
| `src/maxo/utils/`        | Builders, upload, formatting, deeplink/link.                                |
| `butcher/`               | Кодогенерация по свагеру, свой `AGENTS.md`.                                 |

`maxo.dialogs` и `maxo.transport.webhook` портированы из `aiogram_dialog` и
`aiogram-webhook`: при правках держи совместимость их паттернов.

## Неочевидные механизмы

### Типы

- `_MaxoTypeMetaClass` (`types/base.py`) сам оборачивает каждого наследника
  `MaxoType` в `@dataclass(slots=True, kw_only=True)`. Явный `__slots__` в
  классе отключает это.
- `MaxoType` наследует `BaseMethodsFacade` (`types/facades/base.py`), и
  метакласс конфликтует с `ABCMeta`: ни `MaxoType`, ни фасады не могут быть
  `ABC`/`Protocol`. Поэтому `@abstractmethod` на фасадах декоративный, а поля
  вроде `message` объявлены раздвоённо через `if TYPE_CHECKING`. Это
  технический долг до отвязки `MaxoType` от фасада.
- `maxo/types/facades/__init__.py` пуст намеренно: реэкспорт фасадов
  зацикливает импорт через `types/base.py`. Фасад импортируй из конкретного
  модуля: `from maxo.types.facades.chat import ChatMethodsFacade`.
- Loader из `serialization.py` привязывает `Bot` ко всем загруженным типам,
  поэтому update умеет отвечать сам: `await message.send_message(...)`. Вручную
  бот привязывается через `as_(bot)`.
- `Omitted()` - поле не отправляется, `None` в теле - уходит `null`, `None` в
  `Query[...]` превращается в `Omitted()` (`_omit_none_query_values`). Optional
  wire-поле - `Omittable[T] = Omitted()`, поле, которое приходит `null`, -
  `Omittable[T | None]`. Для каждого `Omittable`-поля есть `unsafe_<поле>`,
  кидающий `AttributeIsEmptyError` (образец - `unsafe_sender`).
- Полиморфные типы (updates, attachments, markup, buttons) регистрируются в
  `TAG_PROVIDERS` в `serialization.py`. Union-алиас генерируется, регистрация -
  ручная; без неё `LoadError` в рантайме. Порядок - в `butcher/AGENTS.md`.
- `serialization.py` ещё дампит query (bool -> `"true"`/`"false"`, списки
  через запятую, `datetime` в миллисекунды), грузит таймстемпы в `datetime` с
  `UTC` и подставляет `BotDefaults` (`text_format`, `disable_link_preview`).
  Дефолты получают только методы из ручных алиасов `TypesWithFormat` и
  `TypesWithLinkPreview`: новый метод с `format` или `disable_link_preview`
  добавляй туда.
- `bot/warming_up.py` заранее строит сериализаторы adaptix для всех типов и
  методов; новый тип или метод добавляй и туда.

### Роутинг

```text
Long polling / webhook -> Dispatcher -> Router tree
  -> outer middleware -> filters -> inner middleware -> handler
```

- `Dispatcher` - корневой `Router`; `Router.include(...)` задаёт порядок обхода.
  Первый обработавший update останавливает поиск.
- Фильтры бывают на observer'е (для всех его handler'ов) и на handler'е.
- `UNHANDLED` - ни один handler не подошёл, update идёт в дочерние роутеры.
  `SkipHandler` - пропустить текущий handler и искать дальше в том же
  observer'е, к дочерним роутерам update не идёт.
- После startup-сигналов observers замораживаются: handler или фильтр,
  добавленный позже, даёт ошибку.
- `before_startup`, `after_startup`, `before_shutdown`, `after_shutdown` -
  lifecycle hooks, а не обычные update.
- `message`, `callback_query`, `edited_message` - алиасы `message_created`,
  `message_callback`, `message_edited` для портирования с aiogram. В новом коде
  и docs пиши явные имена.
- Флаги-маркеры хендлеров - `maxo.routing.flags`, инстанс `flags`
  экспортируется из `maxo`.
- Webhook подписывается только на используемые update:
  `collect_used_updates(dispatcher)` обходит роутеры динамически.
- Long polling (`maxo.transport.long_polling`) в docs и examples запускай через
  `Dispatcher.run_polling` (свой event loop) или `Dispatcher.start_polling` (уже
  в async-контексте); класс `LongPolling` - только ради `backoff_config`.
- Поллинг не перехватывает `SIGINT`/`SIGTERM`, но глушит `KeyboardInterrupt`:
  остановкой процесса управляет приложение. Перехват сигналов не добавляй без
  решения мейнтейнера.

### Bot API

- Метод - класс `MaxoMethod[Result]` с `__url__`, `__method__` и маркерами
  полей из `maxo.bot.methods.markers` (`Path`, `Query`, `Header`, `Body`,
  `Form`, `File`); маркеры совпадают с wire-контрактом. `Result` - тип ответа
  после десериализации.
- `Bot` привязывает методы через `unihttp.bind_method`; ручные
  passthrough-методы не пиши.
- Метод, который MAX убрал или перестал поддерживать, помечается
  `@deprecated(..., stacklevel=2)` из `typing_extensions` на классе. В unihttp
  своей пометки нет, но `bind_method` создаёт экземпляр метода при каждом
  вызове, поэтому `DeprecationWarning` срабатывает и на `bot.<метод>()`, а
  `stacklevel=2` указывает на строку пользователя. Статически mypy и IDE
  подсвечивают импорт класса, но не вызов через `Bot`. Сгенерированному
  методу пометку ставит butcher (`DEPRECATED_METHODS`). Импорты устаревших
  символов внутри maxo и в тестах - с `# type: ignore[deprecated]`: в mypy
  включён код `deprecated`.
- `MaxApiClient` добавляет российский trusted CA, `Authorization`,
  `User-Agent`, маппинг ошибок API и превращает HTTP 200 с `"success": false`
  или с `error_code` в 400. Исключение - `AddMembers`: он отдаёт частичный результат, и это
  поведение не меняй без отдельного теста и документации.
- `Bot.download` принимает URL или `AttachmentPayload` и пишет в файл либо
  возвращает `BinaryIO`.

### FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию: `MemoryStorage`,
  `SimpleEventIsolation`, `DefaultKeyBuilder`. Для нескольких процессов -
  Redis storage/isolation.
- Ключ FSM: `{bot_id}:{chat_id}:{user_id}:{destiny}`. Dialogs держат несколько
  стеков через `destiny`, поэтому им нужен
  `DefaultKeyBuilder(with_destiny=True)`; без него `destiny != "default"` даёт
  `ValueError`. `setup_dialogs` ставит такую изоляцию сам, при кастомной FSM
  проверяй совместимость ключей.
- `setup_dialogs(dp)` вызывается после подключения диалогов к роутерам.
- `Dialog` наследует `Router`, но `include()` у него кидает `TypeError`; свои
  update диалог ловит через `IntentFilter`.
- Callback payload виджета - `{intent_id}:{widget_id}:{data}`, по `intent_id`
  грузится нужный контекст. Widget `id` в окне и диалоге стабильны и уникальны.
- `manager.find(widget_id)` возвращает `ManagedWidget`, проксирующий атрибуты
  виджета и знающий `manager`; виджет расширяет его через `managed(manager)`.
- Стек - не больше 100 диалогов (`_STACK_LIMIT`).
- `new_int_id()` (время в мс + random) кодируется в короткую строку, чтобы
  уложиться в лимит длины payload. ID двух диалогов, запущенных в одну
  миллисекунду, могут совпасть - известное ограничение; формат держит короткий
  payload, обходы коллизии требуют изменения публичного контракта.

## Публичный API

- Top-level `maxo` повторяет корень `aiogram`: `Bot`, `Dispatcher`, `Router`,
  `Ctx`, `BaseMiddleware`, `flags`, `html`, `md`, модули `enums`, `methods`,
  `types` и `__version__`. Не расширяй его без причины, остальное импортируется
  из своих модулей.
- Канонические места: update-типы - `maxo.types`; общие и API-исключения -
  `maxo.errors`; dialog-исключения - `maxo.dialogs.api.exceptions`;
  управляющие исключения routing - `maxo.routing.sentinels`.
- `maxo.methods` реэкспортирует `maxo.bot.methods`; `maxo.exceptions` и
  `maxo.filters` - постоянные алиасы `maxo.errors` и `maxo.routing.filters` для
  портирования с aiogram, без предупреждений и без планов на удаление (в отличие
  от переездов внутри пакета, которые кидают `DeprecationWarning`). Новый символ
  добавляй в `__all__` обоих модулей пары; расхождение ловит
  `tests/maxo/test_public_api.py`.
- Новый публичный символ - в ближайший `__init__.py` и его `__all__`.
- Docs и examples импортируют из публичных модулей, не из `maxo._internal`.

## Правила кода

- Только короткое тире `-`, никаких других Unicode-тире.
- Без `from __future__ import annotations` в новых файлах.
- Строки до 88 символов, двойные кавычки, отступ 4 пробела. Формат задают
  `ruff format` и `black` одновременно, дерево - неподвижная точка обоих. Если
  они разошлись на новом коде, перепиши код, а не конфиги. Весь репозиторий
  без отдельной задачи не переформатируй.
- `mypy` в `strict` для `src/maxo`, `tests` и `examples`; публичный код
  аннотирован полностью, в тестах аннотации тоже проверяются.
- `Any`, `cast`, `type: ignore` и отключение lint-правил - только с локальным
  объяснением причины; у `type: ignore` - конкретный код ошибки. В `cast` тип
  передаётся объектом (`cast(Retort, x)`), строкой - только если он
  импортирован под `TYPE_CHECKING`.
- Импорты - на уровне модуля. При импорте модуля - никаких сетевых вызовов,
  env, процессов, файловой системы и прочих side effects, кроме декларативной
  регистрации.
- Пути - `pathlib.Path`.
- Новые модели: `MaxoType` для API, `@dataclass(slots=True)` там, где в
  подсистеме принят dataclass.
- `just lint` гоняет ещё `codespell`, `slotscheck` и `bandit`: учитывай их в
  пользовательском тексте, `__slots__`, dataclass-моделях и security-коде.

## Кодогенерация: butcher

`src/maxo/types`, `src/maxo/enums` и `src/maxo/bot/methods` генерируются из
`max-swagger.json` и `max-swagger.yaml` - источника правды по контракту MAX Bot
API. Изменение контракта синхронизирует метод, типы, enum, сериализацию,
фасады, тесты и документацию; изолированные ручные правки сгенерированных
файлов не делай.

**Прочитай `butcher/AGENTS.md` перед правкой `butcher/`, сгенерированных
файлов или свагеров.** Скилл `.agents/skills/butcher-update` - обёртка над ним,
его `references/manual-layer.md` - перечень ручного слоя поверх генерации.

## Зависимости

- Runtime-зависимость добавляй только по необходимости и с проверкой
  минимальной версии: CI тестирует и `lowest-direct`.
- Extras: `magic_filter`, `dishka`, `redis`, `fastapi`, `preview`. Новый extra -
  это `pyproject.toml`, docs, examples и тесты, которые не требуют внешнего
  сервиса.

## Тесты

- `pytest` с `asyncio_mode = auto`, моки из `unittest.mock` (`AsyncMock` для
  async). Тесты лежат зеркально подсистемам: `tests/maxo`, `tests/maxo_dialog`,
  `tests/maxo_webhook`.
- Без реального MAX API и сети. Тест фиксирует поведение, а не реализацию.
- В каждой тестовой директории `__init__.py` (ruff `INP001`). Общие хелперы -
  в ближайший `conftest.py`, импорт `from .conftest import ...`.
- Готовые хелперы: `mock_manager` в `tests/maxo_dialog/widgets/conftest.py`,
  `create_text_message`/`create_photo_message`/`setup_mock_manager` в
  `tests/maxo_dialog/widgets/input/conftest.py`, test tools из
  `maxo.dialogs.test_tools` (`BotClient`, `MockMessageManager`, memory storage,
  локаторы клавиатуры), фикстуры `tests/maxo_webhook`. Фильтры виджетов читают
  `manager.event` - передай его в `setup_mock_manager`.
- Для dialogs проверяй края: пустой текст, сообщение без body, фильтр с
  `False`, `on_error`, `page=0` и `page > max`, пустой `ListGroup`.
- Изменения hooks и transport сверяй с `tests/maxo_webhook`; проверку секрета
  webhook тестируй в положительном и отрицательном сценарии.
- Цель покрытия - 90%+: `uv run pytest tests/ --cov=src --cov-report=term`.

## Документация и примеры

- Sphinx в `docs/`, страницы в `rst`, changelog - `docs/pages/changelog.md`.
  Новые страницы - в `docs/index.rst` и нужный `toctree`. `docs/_build/` не
  коммить.
- Новая пользовательская возможность - обновить docs и, если уместно,
  `examples/`. README - короткие примеры, подробности - в `docs/pages/`.
- В примерах: явные observers (`message_created`, `message_callback`), алиасы -
  только как совместимость; клавиатуры через
  `maxo.utils.builders.KeyboardBuilder`; magic filter через
  `maxo.integrations.magic_filter.MagicFilter`; webhook через `SimpleEngine`,
  `AiohttpWebAdapter`/`FastApiWebAdapter`, `StaticRouting`, `Security`,
  `StaticSecretToken`, `collect_used_updates`.
- После правок `docs/conf.py`, `_static`, `_extra/llms.txt` или sitemap проверь
  сборку: `uv run sphinx-build -b html docs docs/_build/html`.

## CI

- `lint.yml` (Python 3.14): `ruff check --no-fix`, `black --check`, `mypy`,
  `codespell src examples`, `slotscheck -m maxo`, `bandit -c pyproject.toml src
  -r`. `test.yml`: Python 3.12-3.14 x резолвинг `lowest-direct`/`highest`,
  `just test --cov-report=xml`; матрицу гоняет GitHub, `just test-all` (nox) в
  CI не используется.
- Резолвинг в `test.yml` задаёт `UV_RESOLUTION` на уровне job, а не
  `uv sync --resolution`: `uv run` в рецептах без переменной перерезолвил бы до
  `highest`, и job `lowest-direct` тестировал бы свежие версии. Локально:
  `UV_RESOLUTION=lowest-direct just test`.
- Python ставит `setup-uv` входом `python-version`, отдельного
  `actions/setup-python` нет. Кэш `uv` не настраивается: дефолты уже включают
  его и смотрят на `pyproject.toml`. В `test.yml` нужен
  `cache-suffix: ${{ matrix.dependency-resolution }}`, иначе шесть job делят
  одну запись кэша.
- `build.yml` собирает sdist и wheel, проверяет `twine check --strict` и
  `check_dist.py`; его же через `workflow_call` зовёт `publish.yml`, так что
  публикуется проверенный артефакт. `twine` закреплён в группе `dev` и зовётся
  через `uv run`, не `uvx`, чтобы версия проверяльщика не менялась сама.
- `check_dist.py` - единственный источник правды по содержимому дистрибутива
  (`py.typed`, `russiantrustedca.pem`, лицензии, отсутствие мусора,
  импортируемость из одного колеса). Его зовут CI и `just check-dist`; он на
  голой stdlib и запускается через `uv run --no-project`. `twine check` этих
  отказов не ловит, поэтому скрипт из проверок не убирай.
- `publish.yml` публикует на PyPI по `release: published` через OIDC Trusted
  Publishing (environment `pypi`), сверяет версию артефакта с тегом и
  прикладывает дистрибутив к релизу. Токена PyPI в секретах нет и не должно
  быть. `workflow_dispatch` нет намеренно: он обходил бы сверку версии с тегом.
- `relator.yml` шлёт уведомления о новых issues и PR в Telegram.
- Сторонние actions закреплены по полному SHA с комментарием версии (`zizmor`,
  правило `unpinned-uses`); пины обновляет dependabot. Новый шаг добавляй сразу
  с SHA, `actions/checkout` - с `persist-credentials: false`.
- Меняешь команды разработки - обновляй вместе `justfile`, `AGENTS.md` и
  workflows.

## Перед завершением задачи

- Рабочее дерево проверено, чужие изменения не перезаписаны; локальные
  артефакты (`__pycache__`, `.DS_Store`, кэши линтеров, `coverage.xml`,
  `htmlcov/`, `docs/_build/`) не попали в коммит.
- Измененное поведение покрыто тестами; публичный API, docs и examples
  синхронизированы.
- Прогнаны релевантные проверки; если какая-то не запускалась - названа причина.
- Коммиты - conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), русский
  текст допустим, без `Co-Authored-By`. В PR-шаблоне честно отмечено
  использование ИИ: код может писать ИИ, но его полностью проверяет человек.
