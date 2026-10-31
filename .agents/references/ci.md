# CI и пины версий

## Версия uv

Версия `uv` закреплена в четырёх местах, меняй все сразу:
`[tool.uv] required-version` (источник правды, другой `uv` откажется
работать), `build-system.requires` (`uv_build`), вход `version` у
`astral-sh/setup-uv` в каждом workflow и `pip install uv==...` в
`.readthedocs.yml` (RTD ставит `uv` через `pip`, без пина приедет свежий и
сборка документации упадёт).

## Workflows

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
