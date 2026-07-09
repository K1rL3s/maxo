# Исследование потребления памяти при импорте maxo

Среда:

- Репозиторий: `/Users/k1rles/papka/code/maxo_2`
- Python: CPython 3.14.2, установлен и выбран через `uv`
- Платформа: macOS, aarch64
- Команда синхронизации окружения: `/Users/k1rles/.local/bin/uv sync --all-groups`
- Основной способ замера RSS: `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`
- `psutil` не входит в зависимости проекта, поэтому для воспроизводимых замеров
  внутри `.venv` использовался стандартный модуль `resource`

Важно про единицы измерения:

- В этой среде `ru_maxrss` на macOS возвращается в байтах.
- В таблицах ниже значения RSS указаны в байтах.
- Для чтения человеком можно грубо делить на `1024 * 1024`.

## Что исследовалось

Изначальная жалоба:

```python
import psutil

process = psutil.Process()
print(process.memory_info().rss)

from maxo import *

print(process.memory_info().rss)
```

Ожидание: понять, почему после `from maxo import *` процесс потребляет примерно
на 50 MB больше, и уменьшить причину, а не просто отложить загрузку до первого
обращения к объекту.

## Короткий итог

Основная причина роста RSS при `from maxo import *` - не один большой кеш
внутри `maxo`, а тяжелый import-граф, который тянется top-level экспортом
`Bot`:

- `adaptix`
- `aiohttp`
- `anyio`
- `pydantic`
- `unihttp`
- все типы MAX API
- все методы Bot API
- сериализация и retort-конфигурация

После предварительного импорта основных внешних зависимостей сам `maxo`
добавлял только около 5.3 MB RSS. То есть большая часть роста на простом
импорте - это стоимость обязательного внешнего стека, который импортируется
сразу через публичный `Bot`.

Отдельная реальная runtime-причина была найдена у живого `Bot()`:

- `Bot()` по умолчанию создает retort с `warming_up=True`.
- `warming_up` вызывает `retort.get_loader(...)` и `retort.get_dumper(...)` для
  большого числа типов и методов.
- Adaptix генерирует Python-код сериализаторов и десериализаторов.
- Сгенерированный код и сопутствующие структуры остаются в памяти.
- Adaptix также кладет исходники сгенерированных функций в `linecache`.

Итоговая правка уменьшает именно постоянную память прогретого retort:

- В `src/maxo/serialization.py` используется собственный базовый retort с тем
  же unihttp recipe, но с `debug_trail=DebugTrail.DISABLE`.
- В `src/maxo/bot/warming_up.py` после прогрева удаляются только записи
  `linecache` вида `<adaptix generated ...>`.

## Итоговый эффект

До правки, в этой среде:

- `from maxo import *`: примерно `63.2 MB` итогового RSS
- `from maxo import *; Bot("")`: примерно `90.6 MB` итогового RSS
- `create_retort()`: примерно `85.0 MB` итогового RSS
- `tracemalloc`: `adaptix/_internal/code_tools/compiler.py` занимал примерно
  `6.8 MiB`
- `linecache`: после `Bot("")` было `551` записей `<adaptix generated ...>`
  суммарно на `1,950,175` байт исходников

После правки:

- `from maxo import *`: примерно `62.1 MB` итогового RSS
- `from maxo import *; Bot("")`: примерно `86.1 MB` итогового RSS
- `create_retort()`: примерно `81.6 MB` итогового RSS
- `tracemalloc`: `adaptix/_internal/code_tools/compiler.py` снизился примерно
  до `1.0 MiB`
- `linecache`: после `Bot("")` осталось `0` записей `<adaptix generated ...>`

Выигрыш:

- Прогретый `Bot("")`: примерно `4-5 MB` RSS в этой среде.
- `create_retort()`: примерно `3-4 MB` RSS в этой среде.
- Сам простой импорт `from maxo import *` почти не меняется, потому что его
  основная цена - импорт внешних библиотек и большого числа классов.

## Команды, которые использовались

Установка `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Синхронизация окружения:

```bash
/Users/k1rles/.local/bin/uv sync --all-groups
```

Замер RSS по сценариям:

```bash
.venv/bin/python - <<'PY'
import subprocess
import sys

cases = {
    "empty": "pass",
    "adaptix": "import adaptix",
    "aiohttp": "import aiohttp",
    "unihttp.bind_method": "import unihttp.bind_method",
    "unihttp.clients.base": "import unihttp.clients.base",
    "pydantic": "import pydantic",
    "anyio": "import anyio",
    "from maxo import *": "from maxo import *",
    "from maxo import *; Bot('', warming_up=False)": (
        "from maxo import *\nBot(\"\", warming_up=False)"
    ),
    "from maxo import *; Bot('')": "from maxo import *\nBot(\"\")",
    "create_retort(warming_up=False)": (
        "from maxo.serialization import create_retort\n"
        "create_retort(warming_up=False)"
    ),
    "create_retort()": (
        "from maxo.serialization import create_retort\ncreate_retort()"
    ),
}

for name, stmt in cases.items():
    code = "\n".join(
        [
            "import resource, sys",
            "def rss(): return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss",
            "before = rss()",
            *stmt.splitlines(),
            "after = rss()",
            "print(before, after, after - before, len(sys.modules))",
        ],
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
    )
    print(f"{name}: {result.stdout.strip() or result.stderr.strip()}")
PY
```

Замер модулей, которые импортируются при `from maxo import *`:

```bash
.venv/bin/python - <<'PY'
import subprocess
import sys
import textwrap

code = textwrap.dedent(
    """
    import sys
    from collections import Counter

    before = set(sys.modules)
    from maxo import *
    after = set(sys.modules)

    modules = sorted(after - before)
    counts = Counter(name.split(".")[0] for name in modules)

    print("new_modules", len(modules))
    for name, count in counts.most_common(40):
        print(name, count)

    print("--- selected ---")
    for prefix in (
        "adaptix",
        "aiohttp",
        "unihttp",
        "maxo",
        "pydantic",
        "anyio",
    ):
        selected = [
            module
            for module in modules
            if module == prefix or module.startswith(prefix + ".")
        ]
        print(prefix, len(selected))
    """
)

result = subprocess.run(
    [sys.executable, "-c", code],
    text=True,
    capture_output=True,
    check=True,
)
print(result.stdout)
PY
```

Замер `linecache` после прогрева:

```bash
.venv/bin/python - <<'PY'
from maxo import Bot
import linecache

Bot("")

entries = []
for filename, entry in linecache.cache.items():
    if filename.startswith("<adaptix generated "):
        size, _, lines, _ = entry
        entries.append((filename, size, len(lines)))

print("entries", len(entries))
print("source bytes", sum(size for _, size, _ in entries))
for filename, size, lines in sorted(entries, key=lambda x: x[1], reverse=True)[:20]:
    print(size, lines, filename)
PY
```

Проверка после финальной правки:

```bash
/Users/k1rles/.local/bin/uv run ruff check --no-fix \
  src/maxo/serialization.py src/maxo/bot/warming_up.py

/Users/k1rles/.local/bin/uv run mypy --config-file pyproject.toml

/Users/k1rles/.local/bin/uv run pytest tests/ -q
```

## Сырые RSS-замеры до правки

Первый стабильный замер после установки окружения:

```text
empty: 14778368 14778368 0 56
adaptix: 15187968 41271296 26083328 356
aiohttp: 14548992 39337984 24788992 310
unihttp.bind_method: 14532608 19185664 4653056 98
unihttp.clients.base: 14548992 25362432 10813440 180
pydantic: 14385152 21577728 7192576 108
anyio: 14794752 25395200 10600448 174
maxo star: 14663680 63225856 48562176 837
```

Вывод из этого замера:

- Один только `adaptix` давал примерно `26.1 MB`.
- Один только `aiohttp` давал примерно `24.8 MB`.
- `anyio` давал примерно `10.6 MB`.
- `pydantic` давал примерно `7.2 MB`.
- `unihttp.clients.base` давал примерно `10.8 MB`.
- `from maxo import *` давал примерно `48.6 MB` прироста.

Отдельный важный замер:

```text
deps then maxo: 56803328 62128128 5324800 837
```

Этот сценарий сначала импортировал тяжелые зависимости:

```python
import adaptix
import aiohttp
import anyio
import pydantic
import unihttp.bind_method
import unihttp.clients.base
```

Потом импортировал `maxo`:

```python
from maxo import *
```

Результат: после уже импортированных внешних зависимостей сам `maxo` добавил
примерно `5.3 MB`. Это ключевой факт: большая часть `50 MB` - это не внутренний
кеш maxo, а импорт внешнего стека и большого графа модулей.

Замер создания retort и Bot до правки:

```text
maxo star + Bot false: 14548992 62455808 47906816 837
maxo star + Bot true: 15056896 90587136 75530240 837
serialization false: 14581760 62799872 48218112 837
serialization true: 14647296 85049344 70402048 837
```

Вывод:

- `Bot(warming_up=False)` почти не добавлял памяти сверх импорта.
- `Bot()` с `warming_up=True` заметно увеличивал RSS.
- `create_retort()` с прогревом тоже заметно увеличивал RSS.
- Значит отдельная runtime-причина - именно прогрев adaptix retort.

## Модульный import-граф до правки

Количество новых модулей после `from maxo import *`:

```text
new_modules 781
maxo 280
adaptix 110
aiohttp 40
pydantic 40
anyio 31
asyncio 30
unihttp 25
email 19
attr 13
importlib 8
yarl 8
attrs 6
aiohappyeyeballs 5
compression 5
idna 5
re 5
urllib 5
json 4
multidict 4
propcache 4
```

Выборочно:

```text
adaptix 110
aiohttp 40
unihttp 25
maxo 280
pydantic 40
anyio 31
```

Почему это происходит:

- `src/maxo/__init__.py` экспортирует `Bot`.
- `Bot` импортирует `MaxApiClient`, `BotDefaults`, все методы Bot API,
  `create_retort_with_bot`, `AttachmentPayload`, `MaxoType`.
- `MaxApiClient` импортирует `aiohttp`, `anyio`, `unihttp.clients.aiohttp`.
- `serialization.py` импортирует `adaptix`, `unihttp.serializers.adaptix`,
  все полиморфные update-типы, attachments, buttons, markup и т.д.
- `maxo.types.__init__` импортирует весь набор API-моделей.
- `maxo.bot.methods.__init__` импортирует весь набор методов Bot API.

Это объясняет, почему простой top-level импорт тяжелый.

## Tracemalloc до правки

Для `from maxo import *` верхушка `tracemalloc` выглядела так:

```text
<frozen importlib._bootstrap_external>:0: size=15.3 MiB
dataclasses.py:0: size=2078 KiB
<frozen abc>:0: size=1401 KiB
<frozen importlib._bootstrap>:0: size=1108 KiB
typing.py:0: size=956 KiB
attr/_make.py:0: size=674 KiB
src/maxo/types/base.py:0: size=574 KiB
enum.py:0: size=515 KiB
annotationlib.py:0: size=405 KiB
```

Вывод:

- На простом импорте значительная часть Python heap уходит в importlib-кеши,
  dataclass/typing/abc и создание большого числа классов.
- Это согласуется с тем, что импортируется много типов и внешних библиотек.

Для `Bot("")` до правки верхушка `tracemalloc` показывала уже другую важную
причину:

```text
adaptix/_internal/code_tools/compiler.py:0: size=6837 KiB
adaptix/_internal/morphing/model/basic_gen.py:0: size=835 KiB
adaptix/_internal/provider/provider_wrapper.py:0: size=694 KiB
adaptix/_internal/retort/builtin_mediator.py:0: size=649 KiB
adaptix/_internal/datastructures.py:0: size=408 KiB
adaptix/_internal/retort/searching_retort.py:0: size=406 KiB
adaptix/_internal/retort/request_bus.py:0: size=395 KiB
```

Вывод:

- При создании `Bot("")` с `warming_up=True` появляется постоянный расход в
  adaptix generated-code и retort-структурах.
- Это уже не просто цена импорта, а память, которая остается в живом объекте
  `Bot`.

## Проверка linecache до правки

После `Bot("")` в `linecache` были записи с исходниками сгенерированных
adaptix-функций:

```text
entries 551
source bytes 1950175
11446 302 <adaptix generated model_loader_ChatMember>
10962 289 <adaptix generated model_loader_Chat>
10962 289 <adaptix generated model_loader_Chat 1>
10962 289 <adaptix generated model_loader_Chat 2>
7988 214 <adaptix generated model_loader_BotInfo>
7568 201 <adaptix generated model_loader_UserWithPhoto>
7554 196 <adaptix generated model_dumper_SendMessage>
5993 162 <adaptix generated model_loader_User>
5914 153 <adaptix generated model_dumper_EditBotInfo>
5760 153 <adaptix generated model_dumper_GetMessages>
```

Причина в adaptix:

```python
linecache.cache[unique_filename] = (
    len(source),
    None,
    source.splitlines(keepends=True),
    unique_filename,
)
```

То есть исходники сгенерированных функций сохранялись в глобальном
`linecache.cache`. Это помогает отладочным traceback, но для production-runtime
создает постоянную память после прогрева.

## Эксперимент с DebugTrail

`unihttp.serializers.adaptix.serialize.DEFAULT_RETORT` создается как обычный
`Retort(...)`, а у adaptix default:

```python
Retort(..., debug_trail=DebugTrail.ALL)
```

Эксперимент с заменой базового retort:

```text
current true 14991360 85082112 70090752 837
disabled true 14647296 82526208 67878912 837
first true 14680064 83722240 69042176 837
```

Вывод:

- Один только `DebugTrail.DISABLE` давал около `2 MB` выигрыша RSS.
- Это полезно, но не объясняет всю память.
- Основная видимая Python-heap экономия приходила после удаления generated
  source из `linecache`.

## Почему не был оставлен lazy-import подход

Во время исследования был временный эксперимент:

- сделать top-level `maxo.__getattr__`;
- сделать `maxo.types` и `maxo.bot.methods` ленивыми;
- сделать методы `Bot` ленивыми через дескриптор.

Этот подход действительно резко уменьшал память до первого обращения к
объектам, например `import maxo` становился очень дешевым.

Но он был отвергнут по правильной причине:

- это не уменьшает реальную стоимость используемых компонентов;
- это в основном переносит аллокации с import-time на first-use;
- пользователь явно попросил не убирать симптомы, а разобраться в причине.

Поэтому финальная правка не использует lazy-import как основной механизм.

## Что именно изменено

### `src/maxo/serialization.py`

Было:

```python
from unihttp.serializers.adaptix.serialize import DEFAULT_RETORT
```

И далее:

```python
extended = DEFAULT_RETORT.extend(...)
return typing.cast(Retort, extended)
```

Стало:

```python
from adaptix import Chain, DebugTrail, P, Retort, as_sentinel, dumper, loader
from adaptix._internal.morphing.generic_provider import TypeHintTagsUnwrappingProvider
from unihttp.http import UploadFile
from unihttp.omitted import Omitted as UnihttpOmitted
from unihttp.serializers.adaptix.provider import method_provider
```

Добавлен базовый retort с тем же recipe, который использовал unihttp:

```python
_BASE_RETORT = Retort(
    recipe=[
        as_sentinel(UnihttpOmitted),
        TypeHintTagsUnwrappingProvider(),
        method_provider(),
        dumper(UploadFile, lambda x: x.to_tuple()),
    ],
    debug_trail=DebugTrail.DISABLE,
)
```

И `_create_retort()` теперь расширяет `_BASE_RETORT`:

```python
return _BASE_RETORT.extend(...)
```

Почему это корректно:

- Recipe повторяет recipe `unihttp.serializers.adaptix.serialize.DEFAULT_RETORT`.
- Сохраняются:
  - `as_sentinel(Omitted)`;
  - `TypeHintTagsUnwrappingProvider()`;
  - `method_provider()`;
  - `dumper(UploadFile, lambda x: x.to_tuple())`.
- Меняется только debug trail adaptix.
- Сериализационные тесты прошли.

### `src/maxo/bot/warming_up.py`

Добавлено:

```python
import linecache
```

Добавлена функция:

```python
def _drop_generated_sources() -> None:
    for filename in tuple(linecache.cache):
        if filename.startswith("<adaptix generated "):
            linecache.cache.pop(filename, None)
```

После прогрева:

```python
_drop_generated_sources()
```

Почему это корректно:

- Удаляются только `linecache`-записи с именами `<adaptix generated ...>`.
- Скомпилированные функции, их bytecode и closures остаются.
- Retort продолжает работать.
- Меняется только возможность получить красивый исходник generated-функции из
  `linecache`.
- Все тесты прошли.

## Сырые RSS-замеры после правки

Финальный повторный замер:

```text
empty: 14614528 14614528 0 56
adaptix: 14778368 41353216 26574848 356
aiohttp: 14483456 39206912 24723456 310
unihttp.bind_method: 14467072 18677760 4210688 98
unihttp.clients.base: 14614528 24330240 9715712 180
pydantic: 15040512 22331392 7290880 108
anyio: 14761984 25067520 10305536 174
from maxo import *: 14909440 62128128 47218688 837
from maxo import *; Bot('', warming_up=False): 15040512 61833216 46792704 837
from maxo import *; Bot(''): 14581760 86130688 71548928 837
create_retort(warming_up=False): 14663680 62603264 47939584 837
create_retort(): 14630912 81608704 66977792 837
```

Отдельный контроль linecache:

```text
0
```

Это количество записей `linecache.cache`, у которых имя начинается с
`<adaptix generated ` после `Bot("")`.

## Tracemalloc после правки

После финальной правки `tracemalloc` для `Bot("")`:

```text
<frozen importlib._bootstrap_external>:0: size=15.3 MiB
dataclasses.py:0: size=2597 KiB
<frozen abc>:0: size=1429 KiB
<frozen importlib._bootstrap>:0: size=1108 KiB
adaptix/_internal/code_tools/compiler.py:0: size=1023 KiB
typing.py:0: size=953 KiB
adaptix/_internal/morphing/model/basic_gen.py:0: size=801 KiB
adaptix/_internal/provider/provider_wrapper.py:0: size=693 KiB
attr/_make.py:0: size=673 KiB
adaptix/_internal/retort/builtin_mediator.py:0: size=596 KiB
src/maxo/types/base.py:0: size=567 KiB
```

Сравнение:

- До правки `adaptix/_internal/code_tools/compiler.py`: примерно `6837 KiB`.
- После правки: примерно `1023 KiB`.

Это главный подтвержденный эффект.

## Почему `from maxo import *` все еще тяжелый

Потому что top-level public API сейчас экспортирует:

```python
Bot
Dispatcher
Router
Ctx
BaseMiddleware
```

Самый тяжелый символ здесь - `Bot`.

Цепочка:

```text
maxo.__init__
  -> maxo.bot.bot.Bot
  -> MaxApiClient
  -> aiohttp / anyio / unihttp aiohttp client
  -> create_retort_with_bot
  -> adaptix / unihttp adaptix serializer
  -> maxo.types
  -> maxo.routing.updates
  -> maxo.bot.methods
```

Из-за этого `from maxo import *` равнозначен импорту почти всего runtime-ядра
бота, transport HTTP-клиента, сериализации и API-моделей.

Чтобы радикально уменьшить именно простой импорт, есть только архитектурные
варианты:

1. Убрать `Bot` из top-level `maxo`.
2. Сделать top-level экспорты ленивыми через `__getattr__`.
3. Разделить `Bot` и `MaxApiClient`, чтобы импорт класса `Bot` не импортировал
   `aiohttp` до запуска клиента.
4. Сделать `maxo.types.__init__` и `maxo.bot.methods.__init__` ленивыми.
5. Пересмотреть зависимость от adaptix/unihttp на import-time.

Но пункты 2-4 в основном переносят часть расходов на первое использование. Они
полезны для CLI startup и cold import, но не уменьшают стоимость реально
используемого `Bot` так, как это делает чистка generated-source после прогрева.

## Почему не получилось убрать все 50 MB

Потому что эти 50 MB состоят из нескольких слоев:

1. Python interpreter baseline.
2. Импорт `adaptix` и его внутренних подсистем.
3. Импорт `aiohttp` и сетевого стека.
4. Импорт `anyio`.
5. Импорт `pydantic`, который тянется через зависимости.
6. Импорт большого числа dataclass API-моделей `maxo`.
7. Импорт всех Bot API method-классов.
8. Импорт routing/update типов.
9. Для `Bot()` - прогрев adaptix retort.

Финальная правка уменьшает пункт 9. Это реальная runtime-память живого
прогретого бота.

Пункты 2-8 не являются кешем, который можно просто почистить:

- это импортированные модули;
- классы;
- dataclass metadata;
- typing objects;
- enum objects;
- функции;
- descriptors;
- внутренние структуры сторонних библиотек.

Их можно уменьшать только изменением архитектуры импорта или заменой
зависимостей.

## Риски текущей правки

Риск 1: менее подробные ошибки adaptix.

- `DebugTrail.DISABLE` может уменьшить количество отладочной информации,
  которую adaptix добавляет при ошибках загрузки/дампа.
- Функциональное поведение сериализации не должно измениться.
- Тесты сериализации прошли.

Риск 2: generated-фреймы в traceback не смогут показать исходник через
`linecache`.

- Bytecode функций остается.
- Функции продолжают работать.
- Потеряется удобство просмотра generated source в traceback/debugger.
- Для production runtime это приемлемый tradeoff ради памяти.

Риск 3: зависимость от внутреннего формата имени `<adaptix generated ...>`.

- Сейчас adaptix использует именно такой формат.
- Если adaptix изменит формат имен, чистка может перестать находить записи.
- Это безопасная деградация: память снова станет выше, но поведение не
  сломается.

## Проверки

Точечные проверки:

```text
ruff: All checks passed
mypy: Success: no issues found in 668 source files
pytest tests/maxo/test_serialization.py tests/maxo/bot/test_bot.py -q:
18 passed
```

Полная проверка:

```text
pytest tests/ -q:
955 passed in 14.36s
```

## Измененные файлы

```text
src/maxo/serialization.py
src/maxo/bot/warming_up.py
```

Текущий diff по смыслу:

- Собственный `_BASE_RETORT` с recipe unihttp и `DebugTrail.DISABLE`.
- `_create_retort()` расширяет `_BASE_RETORT`.
- После `warming_up_retort()` удаляются generated-source записи adaptix из
  `linecache`.

## Рекомендации для дальнейшей работы

Если цель - уменьшить память именно после простого `from maxo import *`, нужны
архитектурные изменения public import surface:

1. Измерить, насколько допустимо убрать `Bot` из top-level `maxo`.
2. Если top-level API менять нельзя, рассмотреть lazy `__getattr__` для
   `maxo.__init__`, но честно документировать, что это cold-import оптимизация.
3. Развязать `Bot` и `MaxApiClient`, чтобы импорт класса `Bot` не тянул
   `aiohttp`.
4. Развязать `Bot` и `serialization`, чтобы retort собирался при создании
   `Bot`, а не при импорте класса.
5. Развязать `maxo.types.__init__`, чтобы импорт одного типа не грузил все
   модели API.
6. Развязать `maxo.bot.methods.__init__`, чтобы импорт одного метода не грузил
   все методы Bot API.
7. Добавить benchmark-тест памяти в `tests` или отдельный dev-script, чтобы
   видеть регрессии.

Если цель - уменьшить память рабочего бота после создания `Bot()`, следующие
направления более перспективны:

1. Пересмотреть список `_types` и `_methods` в `warming_up.py`.
2. Прогревать только реально используемые направления:
   - только loaders;
   - только dumpers;
   - только update types, которые реально подписаны через `collect_used_updates`.
3. Сделать режим прогрева конфигурируемым:
   - `warming_up=False`;
   - `warming_up="updates"`;
   - `warming_up="methods"`;
   - `warming_up="all"`.
4. Измерить latency первого запроса без полного прогрева и сравнить с экономией
   памяти.
5. Если нужен максимальный production-memory режим, добавить опцию, которая
   отключает debug trail и чистит generated source явно.

## Главный вывод

Полностью убрать прирост `from maxo import *` без изменения архитектуры импортов
нельзя, потому что основная часть памяти - это импортированный внешний стек и
сотни классов API-моделей.

Найденная и исправленная реальная причина внутри runtime maxo - память,
оставшаяся после прогрева adaptix retort:

- debug trail;
- generated source в `linecache`;
- связанные generated-code структуры.

Эта часть уменьшена без lazy-import подхода и без изменения публичного
поведения сериализации.
