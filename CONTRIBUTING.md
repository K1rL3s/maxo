# Руководство для контрибьюторов

Благодарю за интерес к maxo, это руководство поможет вам быстро начать вносить вклад в проект.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) `0.11.28` - менеджер пакетов. Версия закреплена в `pyproject.toml` через `required-version`, другая версия откажется работать: `uv self update 0.11.28`
- [just](https://github.com/casey/just) - запуск команд (опционально, но рекомендуется)

## Начало работы

1. Сделайте форк и клонируйте репозиторий:

```bash
git clone https://github.com/<ваш-username>/maxo.git
cd maxo
```

2. Установите зависимости для разработки:

```bash
uv sync --all-groups
```

Это установит все зависимости: линтеры, тесты, документацию, кодогенерацию и опциональные расширения (`magic_filter`, `dishka`, `redis`, `fastapi`, `preview`).

## Проверка кода

Перед отправкой PR убедитесь, что код проходит все проверки.

С помощью `just`:

```bash
just lint          # ruff, black, codespell, slotscheck, bandit
just mypy          # строгая проверка типов
just test          # pytest с покрытием
just butcher-test  # тесты генератора, их гоняет CI
just test-all      # nox - тесты на Python 3.12, 3.13, 3.14
just all           # всё вместе
```

Или напрямую, теми же командами, что и CI:

```bash
uv run ruff check --no-fix .
uv run black --check .
uv run mypy --config-file pyproject.toml
uv run codespell src examples
PYTHONPATH=src uv run slotscheck -m maxo
uv run bandit -c pyproject.toml src -r
uv run pytest tests/ --cov=src --cov-report=term
uv run --group butcher pytest butcher/tests
```

Флаги важны: `ruff` настроен с `fix = true`, поэтому без `--no-fix` он правит файлы вместо проверки, а `bandit` без `-c pyproject.toml` не видит секцию `skips` и падает на собственном коде проекта. Рецепты `just ruff` и `just black` меняют файлы намеренно - это форматирование, а не проверка.

## Стиль кода

- Форматирование: **ruff format** + **black**, 88 символов на строку, двойные кавычки
- Линтер: **ruff** с включённым набором правил `ALL` (подробности в `pyproject.toml`)
- Типизация: **mypy** в строгом режиме (`strict = true`)
- Все публичные API должны иметь аннотации типов

## Кодогенерация

`src/maxo/types`, `src/maxo/enums` и `src/maxo/bot/methods` генерируются из `max-swagger.json` в корне репозитория. Не правьте эти файлы руками: изменения перезапишет следующий прогон генератора.

```bash
just butcher       # регенерация по max-swagger.json
just butcher-test  # тесты самого генератора
```

Правила генерации и оверрайды описаны в [`butcher/AGENTS.md`](butcher/AGENTS.md).

## Документация

Документация лежит в `docs/`, собирается Sphinx, пишется на русском языке. Публичные docstring тоже русскоязычные.

```bash
just docs
```

Сборка кладёт результат в `docs/_build/` - это локальный артефакт, не коммитьте его. `docs/pages/changelog.md` генерируется из GitHub Releases при сборке, править его руками не нужно.

## Отправка изменений

1. Создайте ветку от `master`:

```bash
git checkout -b feature/название   # для нового функционала
git checkout -b fix/название       # для исправлений
```

2. Внесите изменения, напишите тесты и убедитесь, что `just all` проходит.

3. Создайте Pull Request в ветку `master`. Заполните шаблон PR: тип изменения, описание, тестовая конфигурация.

`uv.lock` в репозитории игнорируется - не добавляйте его в коммит.

## Кодекс поведения

Участвуя в проекте, вы соглашаетесь с [Кодексом поведения](.github/CODE_OF_CONDUCT.md).
