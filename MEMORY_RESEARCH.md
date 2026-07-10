# Исследование потребления памяти maxo

Среда:

- Репозиторий: `/Users/k1rles/papka/code/maxo_2`
- Python: CPython 3.14.2, установлен через `uv`
- Платформа: macOS, aarch64
- RSS меряется как текущий resident set через `ps -o rss=`, а не через
  `resource.getrusage().ru_maxrss`: `ru_maxrss` возвращает пик, и на нём не
  видно разницы между живыми объектами и мусором
- Каждый сценарий запускается в отдельном процессе, берётся медиана 5 запусков

Два окружения:

- prod-подобное: `uv pip install -e .` без extras, `pydantic` отсутствует
- dev: `uv sync --all-groups`, `pydantic` подтянут через `maxo[fastapi]`

## Короткий итог

Изначальная жалоба: после `from maxo import *` и создания `Bot()` процесс
занимает заметно больше памяти, чем ожидается.

Память складывается из трёх слоёв, и только два первых относятся к maxo:

| Слой                                   | Стоимость (prod) | Чиним? |
|----------------------------------------|------------------|--------|
| Интерпретатор                          | ~15 MB           | нет    |
| `import maxo` (adaptix, aiohttp, anyio) | ~37 MB          | нет, это цена зависимостей |
| Прогрев retort в `Bot()`                | ~20 MB          | **да, стало ~4 MB** |

Внутри третьего слоя нашлось две настоящих причины, обе исправлены:

1. **Chained-провайдеры maxo ломали кеш кодогенерации adaptix.** Одна и та же
   модель компилировалась до 26 раз. Всего 551 сгенерированная функция вместо
   250.
2. **Циклический мусор прогрева не собирался.** Кодогенерация adaptix оставляет
   много циклов (исключения `CannotProvide` с трейсбеками). Полная сборка
   мусора после `import maxo` почти не запускается, мусор копится, пик держит
   арены, которые CPython не отдаёт ОС, и пик становится постоянным RSS.

Собственный код `maxo` (280 модулей, сотни dataclass-моделей) стоит всего
**4.7 MB**. Это проверяется прямым замером: если сначала импортировать
`adaptix`, `aiohttp`, `anyio`, `pydantic`, `unihttp`, а потом `maxo`, прирост
составляет 4.7 MB.

## Результат

`Bot("")` с прогревом, медиана 5 запусков:

| Сценарий                    | Было      | Стало     | Разница         |
|-----------------------------|-----------|-----------|-----------------|
| prod: `Bot("")`             | 73.5 MB   | 56.7 MB   | **-16.8 MB**    |
| prod: `Bot("")` x2          | 80.2 MB   | 59.7 MB   | -20.5 MB        |
| prod: `Bot("")` x4          | 97.0 MB   | 64.6 MB   | **-32.4 MB**    |
| dev: `Bot("")`              | 80.9 MB   | 62.6 MB   | -18.3 MB        |
| dev: `Bot("")` x4           | 104.0 MB  | 71.1 MB   | -32.9 MB        |
| Сгенерированных функций     | 551       | 250       | -55%            |
| Время `Bot()`               | ~560 ms   | ~470 ms   | -16%            |

Каждый дополнительный бот в процессе стоил 7.3 MB, теперь 2.6 MB.

Прогрев не стал медленнее, он стал быстрее: компилируется вдвое меньше кода.

## Причина 1: chained-провайдеры ломали кеш кодогенерации

`ModelLoaderProvider` в adaptix кеширует сгенерированный загрузчик через
`mediator.cached_call(self._make_loader, ..., field_loaders=..., ...)`. Ключ
кеша включает загрузчики полей модели.

`ChainingProvider._make_chain` возвращает **новый объект функции** на каждый
запрос:

```python
def _make_chain(self, first, second):
    def chain_processor(data):
        return second(first(data))
    return chain_processor
```

maxo вешает chained-провайдеры почти на всё:

- `has_tag_provider` - `Chain.FIRST` loader и `Chain.LAST` dumper на 56 типов
  (все attachments, buttons, markup, updates)
- `_set_method_defaults` - `Chain.FIRST` dumper
- `Attachments.to_request()` - `Chain.FIRST` dumper
- привязка бота в `create_retort_with_bot` - `Chain.LAST` loader на **каждый**
  `MaxoType`

Из-за этого загрузчик каждого вложенного поля был свежим объектом, ключ кеша
родительской модели не совпадал, и родитель компилировался заново на каждом
пути, по которому до него можно дойти. Дальше это каскадом шло вверх.

Замер до правки, `Bot("")`:

```text
generated closures: 551  distinct: 179  extra compiles: 372
  26x <adaptix generated model_loader_AudioAttachment>
  26x <adaptix generated model_loader_ContactAttachmentPayload>
  26x <adaptix generated model_loader_FileAttachment>
  26x <adaptix generated model_loader_Keyboard>
  26x <adaptix generated model_loader_PhotoAttachment>
  25x <adaptix generated model_loader_ContactAttachment>
  22x <adaptix generated model_loader_MessageBody>
  10x <adaptix generated model_loader_Message>
```

Что чистый adaptix дедуплицирует корректно, проверяется на модели без
chained-провайдеров: `Inner`, использованный в четырёх местах, компилируется
один раз.

**Правка.** `src/maxo/_internal/adaptix/chaining.py`: `CachingChainingProvider`
переопределяет `_wrap_handler` и кеширует композицию через
`mediator.cached_call`. Композиция чистая, для одной пары функций достаточно
одного объекта. Кеш живёт в `_call_cache` конкретного retort, а не в
провайдере: провайдеры в maxo объявлены на уровне модуля, и кеш на провайдере
удерживал бы загрузчики мёртвых ботов.

Помощники `chained_loader` и `chained_dumper` повторяют интерфейс
`adaptix.loader(..., chain=...)` и `adaptix.dumper(..., chain=...)`.

После правки все загрузчики компилируются ровно один раз:

```text
loader compiles 104  distinct 104  dups 0
dumper compiles 146  distinct  75  dups 71
```

Оставшиеся 71 дубликат dumper'ов - ограничение adaptix, не maxo:
`BuiltinSievesMaker._create_sieve` создаёт новую lambda на каждый вызов, из-за
чего `OutputNameLayout` не сравнивается на равенство и кеш `_make_dumper`
промахивается. Это стоит копейки после правки причины 2 (проверено: мемоизация
sieves не меняет RSS), и лезть туда не нужно. Стоит завести issue в adaptix.

## Причина 2: циклический мусор прогрева не собирался

Это оказалось главным.

После правки причины 1 живых объектов у `Bot()` остаётся всего **2.4 MB**
(`tracemalloc`), а RSS растёт на **16 MB**. Разница - транзиентный мусор
кодогенерации: пик Python heap, который держит арены. CPython отдаёт арену ОС,
только когда она полностью пуста, а долгоживущий сгенерированный код
фрагментирует их.

Ключевой замер: если выключить сборщик циклов на время прогрева, RSS
взрывается.

```text
current (default gc)   rss=  68.6  warm_delta=  16.3
gc.disable()           rss= 154.0  warm_delta= 101.5
```

То есть кодогенерация adaptix оставляет ~100 MB циклического мусора, и его
разбирает только сборщик циклов. Исключения `CannotProvide`, которыми adaptix
ищет провайдеров, тянут за собой трейсбеки и фреймы - это циклы.

Дальше: полная сборка (поколение 2) в CPython запускается, когда
`long_lived_pending / long_lived_total > 25%`. После `import maxo` в поколении
2 уже сотни тысяч объектов, поэтому полная сборка почти не срабатывает. Мусор
прогрева переживает нулевое и первое поколения, оседает во втором и лежит там
до конца прогрева.

`gc.freeze()` переносит всё уже созданное в постоянное поколение.
`long_lived_total` обнуляется, полные сборки начинают запускаться сразу, мусор
освобождается по ходу дела, и пик не набирается.

Замеры, 3 запуска на вариант:

```text
1 baseline                 delta= 16.2 / 16.4 / 16.5   time= 495ms
2 collect() per type       delta= 15.5 / 15.1 / 15.1   time= 1332ms
3 collect(1) per type      delta= 15.5 / 15.5 / 15.5   time=  511ms
4 freeze/unfreeze          delta=  6.8 /  6.4 /  6.7   time=  495ms
5 freeze + collect/type    delta=  6.5 /  6.6 /  6.5   time=  543ms
6 freeze + thr(2000,3,3)   delta=  6.0 /  5.7 /  5.4   time=  518ms
```

Вариант 4 даёт почти весь выигрыш и не стоит ничего по времени. Варианты 5 и 6
добавляют мало и трогают чужие настройки GC.

**Правка.** `eager_cycle_collection()` в `src/maxo/bot/warming_up.py` -
контекстный менеджер вокруг прогрева:

```python
if not gc.isenabled() or gc.get_freeze_count():
    yield
    return

gc.freeze()
try:
    yield
finally:
    gc.unfreeze()
```

Две проверки важны:

- `gc.get_freeze_count()` - если процесс уже заморожен (типичный preload перед
  `fork` в gunicorn или uwsgi), `gc.unfreeze()` сломал бы чужой copy-on-write.
  Заодно в таком процессе оптимизация уже работает сама.
- `gc.isenabled()` - если пользователь выключил GC, freeze ничего не даст.

`finally` обязателен: без него исключение в прогреве оставило бы процесс
замороженным навсегда.

## Причина 3: import-граф. Не чинится внутри maxo

`import maxo` стоит 37 MB (prod) или 43 MB (dev). Разбивка:

```text
baseline                 15.5 MB
pydantic                +  6.0 MB
adaptix                 + 24.4 MB   (9.2 MB, если pydantic не установлен)
aiohttp                 + 21.9 MB
anyio                   +  8.5 MB
собственный код maxo    +  4.7 MB
```

Два наблюдения:

1. `adaptix` при импорте безусловно тянет `pydantic`, если тот установлен:
   `adaptix/_internal/type_tools/fundamentals.py` проверяет
   `HAS_SUPPORTED_PYDANTIC_PKG` и делает `from pydantic import BaseModel`.
   `pydantic` не является зависимостью `maxo`: он приезжает через
   `maxo[fastapi]`. В prod-установке без extras этих 6 MB нет.
2. Всё остальное - модули, классы, dataclass metadata, typing- и enum-объекты.
   Это не кеш, который можно почистить.

Уменьшить именно `import maxo` можно только архитектурно: убрать `Bot` из
top-level, сделать ленивые `__getattr__`, развязать `Bot` и `MaxApiClient`.
Это переносит стоимость на первое использование, а не убирает её, поэтому
здесь не делалось.

## Что изменено

```text
src/maxo/_internal/adaptix/chaining.py         (новый)
src/maxo/_internal/adaptix/__init__.py
src/maxo/_internal/adaptix/has_tag_provider.py
src/maxo/serialization.py
src/maxo/bot/warming_up.py
tests/maxo/bot/test_warming_up.py              (новый)
```

Сохранено из предыдущей итерации:

- собственный `_BASE_RETORT` с recipe unihttp и `debug_trail=DebugTrail.DISABLE`
- чистка `linecache` от `<adaptix generated ...>` после прогрева

## Побочный эффект: `warming_up=False` теперь дороже по памяти

```text
prod, после правок:
Bot("", warming_up=False)          53.1 MB
Bot("", warming_up=False) + работа 66.3 MB
Bot("")                            56.7 MB
```

Ленивая кодогенерация происходит при первом `load`/`dump` в рантайме, вне
`eager_cycle_collection()`, поэтому её циклический мусор снова оседает в
поколении 2. Раньше `warming_up=False` экономил память, теперь наоборот: бот с
прогревом занимает на 10 MB меньше, чем бот без прогрева после первой работы.
Отключать прогрев ради памяти больше не имеет смысла.

## Риски

1. `CachingChainingProvider` зависит от внутренностей adaptix: `ChainingProvider`,
   `ValueProvider`, `LoaderRequest`, `DumperRequest`, `bound`,
   `JSONSchemaOverrideProvider`. maxo и так использует
   `TypeHintTagsUnwrappingProvider` и `OriginSubclassLSC`, но при обновлении
   adaptix это надо проверять. Тест
   `test_warming_up_compiles_every_loader_once` упадёт, если кеш снова
   сломается.
2. `gc.freeze()` - процессная операция. Она пропускается, если GC выключен или
   уже заморожен. Объекты, созданные другими потоками во время прогрева,
   попадут в постоянное поколение и после `gc.unfreeze()` окажутся в поколении
   2, то есть будут собираться реже. Это влияет на производительность GC, не на
   корректность.
3. Чистка `linecache` завязана на формат имени `<adaptix generated ...>`. Если
   adaptix сменит формат, память вырастет, но ничего не сломается.

## Проверки

```text
uv run ruff check --no-fix .                 All checks passed
uv run mypy --config-file pyproject.toml     Success: 670 source files
uv run codespell src examples                чисто
uv run slotscheck -m maxo                    All OK
uv run bandit -c pyproject.toml src -r       0 issues
uv run pytest tests/ -q                      962 passed
```

Отдельно проверено end-to-end на прогретом боте: разбор реального payload MAX,
полиморфный разбор union по тегу, привязка бота ко вложенным типам, маршрутизация
апдейта через `Dispatcher` до хендлера, сериализация `SendMessage` с дефолтами,
сериализация attachment с тегом.

`tests/maxo_dialog/test_transitions.py::test_subdialog` флакает примерно в 1-2%
запусков и до этих правок, и после (8/300 на чистом дереве, 4/300 после). К
памяти отношения не имеет, скорее всего коллизии `new_int_id()`. Стоит завести
отдельную задачу.

## Куда дальше, если понадобится

По убыванию отдачи:

1. Один retort на процесс вместо retort на бота. Сейчас retort зависит от бота
   только через `Chain.LAST` loader `x.as_(bot)`. Если привязку делать через
   `ContextVar`, retort можно шарить между ботами и прогревать один раз. Даст
   ~2.6 MB на каждого бота сверх первого.
2. Issue в adaptix на `BuiltinSievesMaker._create_sieve` и на количество
   циклического мусора при кодогенерации.
3. Issue в adaptix на безусловный импорт `pydantic`, если тот просто установлен
   в окружении.
4. Бенчмарк памяти в CI, чтобы ловить регрессии: числа выше воспроизводятся
   стабильно в пределах 1 MB.
