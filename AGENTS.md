# AGENTS.md - правила разработки maxo для AI-агентов

`maxo` - асинхронный Python-фреймворк для ботов мессенджера MAX
(`https://max.ru`), по API и привычкам близкий к `aiogram`. Инструкции для
агентов, docstring'и публичного API и пользовательская документация - на
русском языке.

`CLAUDE.md` содержит только `@AGENTS.md`; правила для любых агентов держи здесь.
Подсистема с длинными правилами - вложенный `AGENTS.md` (и такой же
`CLAUDE.md`), редкие процедуры - в `.agents/references/`.

## Команды

Проект на `uv`, команды в `justfile`, рецепты сами зовут `uv run`.

```bash
uv sync --all-groups   # все extras, иначе падают тесты интеграций
just lint              # ruff + black + codespell + slotscheck + bandit
just mypy
just test              # аргументы pytest: just test -k dialogs
uv run pytest tests/path/test_file.py::test_name -v
```

- `just ruff` и `just black` правят файлы (`fix = true` в `pyproject.toml`).
  Проверка без правок: `uv run ruff check --no-fix .`, `uv run black --check .`.
- `uv.lock` в `.gitignore`; не коммить его без решения мейнтейнера.

## Границы

- `src/maxo/types`, `src/maxo/enums`, `src/maxo/bot/methods` генерирует
  butcher из `max-swagger.json` + `max-swagger.yaml`. Не правь их изолированно:
  изменение контракта - по скиллу `.agents/skills/butcher-update`, правка
  генератора - по `butcher/AGENTS.md`.
- `maxo.dialogs` и `maxo.transport.webhook` - порты `aiogram_dialog` и
  `aiogram-webhook`: держи совместимость их паттернов.
- Только с решения мейнтейнера: перехват `SIGINT`/`SIGTERM` в поллинге (сейчас
  он лишь глушит `KeyboardInterrupt`), смена поведения `AddMembers` (отдаёт
  частичный результат), расширение top-level `maxo`.

## Неочевидные механизмы

### Типы

- `_MaxoTypeMetaClass` (`types/base.py`) сам оборачивает наследника `MaxoType`
  в `@dataclass(slots=True, kw_only=True)`; слоты отключает
  `class X(MaxoType, slots=False)`. Класс с `__slots__` в теле не трогается:
  `dataclass(slots=True)` пересоздаёт класс, второй раз обернуть нельзя.
- Бота держит только `FacadeMaxoType` (`MaxUpdate`, `Message`) в поле `_bot`;
  реторта его пропускает (`name_mapping(..., skip=["_bot"])`). Привязывает
  `bind_bot` (`types/binding.py`): `Bot.call_method` - к ответу,
  `Dispatcher.feed_update` - к апдейту. Вручную - `obj.as_(bot)`.
- Фасады (`types/facades/`, импорт `from maxo.types.facades import ...`) -
  миксины без состояния. Нужное им (`bot`, `chat_id`, `message`) объявляй
  свойством только под `if TYPE_CHECKING`: рантайм-атрибут с именем поля
  dataclass возьмёт дефолтом, и обязательное поле станет необязательным.
- `Omitted()` - поле не отправляется; `None` в теле уходит `null`; `None` в
  `Query[...]` становится `Omitted()`. Необязательное поле -
  `Omittable[T] = Omitted()`, приходящее `null` - `Omittable[T | None]`. У
  каждого `Omittable`-поля есть `unsafe_<поле>` с `AttributeIsEmptyError`
  (образец - `unsafe_sender`).

### Реестры, которые не обновятся сами

| Добавляешь                                    | Куда ещё                                                   |
|-----------------------------------------------|------------------------------------------------------------|
| Полиморфный подтип (апдейт, вложение, кнопка) | словарь `_*_TAGS` в `serialization.py`, иначе `LoadError`  |
| Метод с `format` / `disable_link_preview`     | `METHODS_WITH_DEFAULTS` в `bot/defaults.py`                |
| Метод                                         | `_METHOD_ROOTS` в `bot/warming_up.py`                      |
| Заливаемое медиа (`UploadType`)               | `MEDIA_ATTACHMENT_FACTORIES` в `bot/bot.py`                |
| Тип апдейта                                   | полный список - в `butcher/AGENTS.md`                      |

### Роутинг

- `Dispatcher` - корневой `Router`; порядок обхода задаёт `Router.include(...)`,
  первый обработавший update останавливает поиск.
- `UNHANDLED` - handler не подошёл, update идёт в дочерние роутеры.
  `SkipHandler` - следующий handler того же observer'а, к дочерним не идёт.
- После startup observers замораживаются: handler или фильтр позже - ошибка.
- В новом коде и docs - явные observers `message_created`, `message_callback`,
  `message_edited`; `message`, `callback_query`, `edited_message` - только
  aiogram-алиасы.
- Поллинг в docs и examples - `Dispatcher.run_polling` (свой loop) или
  `start_polling` (уже в async); `LongPolling` - только ради `backoff_config`.

### Bot API

- Метод - класс `MaxoMethod[Result]` с `__url__`, `__method__` и маркерами из
  `maxo.bot.methods.markers` (`Path`, `Query`, `Header`, `Body`, `Form`,
  `File`). `Bot` привязывает их через `unihttp.bind_method`; ручные
  passthrough-методы не пиши.
- Убранный MAX метод - `@deprecated(..., stacklevel=2)` из `typing_extensions`
  на классе (сгенерированному ставит butcher, `DEPRECATED_METHODS`). Импорт
  устаревших символов в maxo и тестах - с `# type: ignore[deprecated]`.
- Middleware `Bot` превращает HTTP 200 с `"success": false` или `error_code` в
  400. Файловые хосты - через `bot.media` (свой клиент, без токена).

## Публичный API

- Top-level `maxo` повторяет корень `aiogram`; остальное импортируется из своих
  модулей. Новый публичный символ - в ближайший `__init__.py` и его `__all__`.
- Канонические места: update-типы - `maxo.types`; исключения - `maxo.errors`;
  dialog-исключения - `maxo.dialogs.api.exceptions`; управляющие исключения
  routing - `maxo.routing.sentinels`.
- `maxo.exceptions` и `maxo.filters` - постоянные aiogram-алиасы `maxo.errors`
  и `maxo.routing.filters`, как и `maxo.methods` для `maxo.bot.methods`: одна
  строка `from <оригинал> import *` без своего `__all__` (реэкспорт по
  спецификации типизации), новый символ - только в оригинал. Переезд внутри
  пакета - со старым путём, кидающим `DeprecationWarning`.
- Docs и examples не импортируют из `maxo._internal`.

## Правила кода

- Только короткое тире `-`, других Unicode-тире нет.
- Без `from __future__ import annotations` в новых файлах.
- Формат - неподвижная точка `ruff format` и `black` одновременно. Разошлись на
  новом коде - перепиши код, а не конфиги. Весь репозиторий не переформатируй.
- `mypy --strict` и для `tests`, `examples`. `Any`, `cast`, `type: ignore`,
  отключение lint-правила - с комментарием о причине; `type: ignore[код]`.
  `cast` - с типом-объектом, строкой только для импорта под `TYPE_CHECKING`.
- Импорт модуля без side effects (сеть, env, ФС, процессы), кроме
  декларативной регистрации.
- Runtime-зависимость - только по необходимости и с проверкой минимальной
  версии: CI тестирует `lowest-direct` (`UV_RESOLUTION=lowest-direct just test`).
  Новый extra - это `pyproject.toml`, docs, examples и тесты без внешнего
  сервиса.

## Тесты

- `pytest` с `asyncio_mode = auto`, моки из `unittest.mock`. Без реального MAX
  API и сети. Раскладка зеркальна: `tests/maxo`, `tests/maxo_dialog`,
  `tests/maxo_webhook`.
- В каждой тестовой директории `__init__.py` (ruff `INP001`); общие хелперы - в
  ближайший `conftest.py`, импорт `from .conftest import ...`.
- Секрет webhook тестируй в положительном и отрицательном сценарии.
- Цель покрытия - 90%+ (`just test` печатает отчёт).

## Справочники (читай, когда задача их касается)

- `.agents/skills/butcher-update/SKILL.md` - обновление контракта MAX API:
  свагеры, новые типы, методы, апдейты.
- `butcher/AGENTS.md` - правка самого генератора.
- `.agents/references/ci.md` - `.github/workflows`, `.readthedocs.yml`, версия
  `uv`, `check_dist.py`, публикация.
- `.agents/references/dialogs.md` - FSM, `maxo.dialogs` и их тесты.
- `.agents/references/docs.md` - `docs/`, `examples/`, README.

Меняешь команды разработки - обновляй вместе `justfile`, `AGENTS.md`,
workflows и `ci.md`.

## Перед завершением задачи

- Зелёные `just lint`, `just mypy`, `just test`; не запускавшуюся проверку
  назови с причиной.
- Чужие изменения не перезаписаны; артефакты (`__pycache__`, кэши линтеров,
  `coverage.xml`, `htmlcov/`, `docs/_build/`) не в коммите.
- Изменённое поведение покрыто тестами; публичный API, docs и examples
  синхронизированы.
- Коммиты - conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), русский
  текст допустим, без `Co-Authored-By`. В PR-шаблоне честно отмечено
  использование ИИ: код может писать ИИ, но его полностью проверяет человек.
