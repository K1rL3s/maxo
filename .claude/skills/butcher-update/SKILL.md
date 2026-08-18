---
name: butcher-update
description: Use when the MAX Bot API contract changes in maxo - a new max-swagger.json, a new or changed type, enum, method or update - or when regenerating src/maxo/types, src/maxo/enums, src/maxo/bot/methods. Triggers on "обнови сваггер", "новая спека", "новый метод API", "новый апдейт", "перегенерируй типы", "just butcher".
---

# Выпуск обновления MAX Bot API через butcher

Правила живут в `butcher/AGENTS.md` и корневом `AGENTS.md` - они старше этого
файла и при расхождении выигрывают. Здесь только процедура: как провести
изменение контракта от `max-swagger.json` до зелёного CI, ничего не потеряв.

## Железное правило

**Не начинай обновление с `just butcher` в `src/maxo`.**

`just butcher` перезаписывает свои файлы целиком, а не построчно. Всё, что
дописано руками поверх генерации - `factory()`, `to_request()`, алиасы под
aiogram, `generated_url`, `# type: ignore`, поля вне свагера - исчезает.
Замеряно на чистом дереве: генерация поверх `src/maxo` ломает `import maxo`
(`FileAttachmentRequest has no attribute 'factory'`) и даёт 410 ошибок `mypy`
в 60 файлах.

Обновление контракта - это перенос **дельты между двумя генерациями**, а не
замена `src/maxo` выводом генератора.

## Процедура

### 0. Окружение

```bash
uv sync --all-groups
git status --porcelain -- src/maxo   # обязано быть пусто
```

`src/maxo` должен быть без незакоммиченных правок: дельту в него будем смотреть
через `git diff`, и чужие изменения в нём собьют проверку. Сам
`max-swagger.json` уже может быть изменён - это нормально, шаг 1 берёт версию
из `HEAD`.

Снимки клади в `.butcher/` - каталог уже в `.gitignore`. `emit.write` в конце
форматирует вывод через ruff с конфигом проекта, и gitignore этому не мешает
(проверено).

**Одна особенность импортов, чтобы не потерять на ней время.** В снимке импорт
типа, которого ещё нет в `src/maxo/types/`, оказывается в отдельной группе:

```python
from typing import TypeAlias

from maxo.types.message_pinned import MessagePinned   # файла в src/maxo ещё нет

from maxo.types.bot_added_to_chat import BotAddedToChat
```

Причина - `src = ["src", "examples", "tests"]` в `pyproject.toml`: isort считает
модуль first-party, только если он лежит на диске. Это артефакт снимка, а не
поломка; после переноса файла в `src/maxo` группа схлопывается сама. Блок
импортов из снимка не копируй вслепую и в конце шага 4 прогоняй ruff.

### 1. Слепок «до» - на спеке из HEAD

```bash
mkdir -p .butcher
git show HEAD:max-swagger.json > .butcher/spec-before.json
just butcher --spec .butcher/spec-before.json --output-dir .butcher/before
```

### 2. Положить новую спеку

Обнови `max-swagger.json` (скачанная спека или точечная правка). Не редактируй
`src/maxo` на этом шаге.

### 3. Слепок «после» и дельта контракта

Если новая спека добавляет апдейт, сначала выбери фасад-миксин по правилу шага
7 и добавь запись в `CLASS_MIXINS`. Оверрайд меняет базы сгенерированного
класса, поэтому он обязан попасть в снимок `after`.

```bash
just butcher --output-dir .butcher/after
diff -ru .butcher/before .butcher/after
```

Этот diff - и есть всё, что изменение контракта делает с кодом. Он маленький и
не содержит шума от ручного слоя. Если diff пуст, а спека менялась - изменение
не дошло до генерации: проверь `SKIP_SCHEMAS`/`SKIP_OPERATIONS` в
`butcher/overrides.py` и вывод `just butcher` (число типов/методов).

Если запись в `CLASS_MIXINS` добавлена позже, повтори генерацию
`.butcher/after` и заново перенеси затронутый тип. Копирование нового файла до
оверрайда оставит класс в `src/maxo` без фасад-миксина.

### 4. Перенести дельту в `src/maxo`

Для каждого файла из diff:

| Что в дельте                | Что делать в `src/maxo`                                                                    |
|-----------------------------|---------------------------------------------------------------------------------------------|
| Файл изменился              | Применить те же ханки руками, ручной слой файла не трогать.                                  |
| Файл только в `after/`      | Скопировать целиком.                                                                         |
| Файл только в `before/`     | Удалить одноимённый в `src/maxo` - **butcher сам ничего не удаляет**, иначе останется мусор.  |
| `__init__.py` любой из трёх | Скопировать из `after/` дословно: генерируются целиком, вместе с ручными реэкспортами.        |

Перенёс - прогони ruff по затронутым файлам, он схлопнет группу импортов нового
типа:

```bash
uv run ruff check --fix src/maxo
```

Проверь глазами, что не задел ручной слой: `git diff -- src/maxo` не должен
содержать удалений `factory`, `to_request`, `@property`, `# type: ignore`,
`Подражание aiogram`. Полный перечень ручного слоя - `references/manual-layer.md`.

### 5. Найти ближайший аналог и прогрепать его

**Обязательный шаг, а не совет.** Таблица шага 6 может устареть, грep - нет.

Выбери ближайшего родственника тому, что появилось: `MessageRemoved` для нового
апдейта, `GetPinnedMessage` для нового метода, `Chat.link` для нового поля. И:

```bash
grep -rn "MessageRemoved\|message_removed" src/ docs/pages/ examples/ tests/
```

Каждое попадание - кандидат в правку. Так находятся места, которых нет ни в
одной таблице: реестры, ручные списки в документации, примеры.

### 6. Карта касаний

Генератор пишет только `types/`, `enums/`, `bot/methods/`. Всё остальное -
руками. Колонка «как падает» важнее самой правки: громкие пропуски найдёт
`import maxo`, тихие доживут до продакшена.

**Новый тип апдейта:**

| Файл                                          | Что                                                          | Как падает пропуск                            |
|-----------------------------------------------|--------------------------------------------------------------|-----------------------------------------------|
| `butcher/overrides.py`, `CLASS_MIXINS`        | миксин-фасад в базах класса                                  | тихо: на апдейте нет методов ответа           |
| `src/maxo/serialization.py`                   | `has_tag_provider(X, "update_type", UpdateType.X)`           | тихо: `LoadError` в рантайме                  |
| `src/maxo/routing/routers/simple.py`          | `self.x = UpdateObserver[X]()` + запись в `_observers`       | тихо: хендлер некуда зарегистрировать         |
| `src/maxo/routing/facades/<name>.py`          | сам фасад                                                    | -                                             |
| `src/maxo/routing/facades/__init__.py`        | импорт и `__all__`                                           | громко: `ImportError`                         |
| `src/maxo/routing/facades/middleware.py`      | запись в `_FACADES_MAP`                                      | тихо: `ctx["facade"]` не создаётся никогда    |
| `src/maxo/routing/middlewares/update_context.py` | ветка `isinstance`, заполняющая `chat_id`/`user`/`user_id` | тихо и хуже всего: ломаются ключи FSM, диалоги и фильтры |
| `src/maxo/bot/warming_up.py`                  | тип в списке типов                                           | тихо: медленный первый запрос                 |
| `src/maxo/routing/updates/<name>.py`          | deep-модуль депрекейтед-шима                                 | тихо                                          |
| `src/maxo/routing/updates/__init__.py`        | импорт и `__all__` шима                                      | тихо                                          |
| `tests/maxo/routing/updates/test_deprecation.py` | новый модуль в `parametrize`                              | тихо                                          |
| `docs/pages/botapi/updates.rst`               | блок `.. autoclass:: maxo.types.X`                           | тихо: апдейта нет в документации              |
| `docs/pages/event-handling/routers.rst`       | строка в таблице «Доступные события»                         | тихо                                          |
| `examples/all_updates.py`                     | хендлер                                                      | тихо: пример перестаёт быть «всеми апдейтами» |

`collect_used_updates` правок **не требует** - он обходит `observers`
динамически.

**Новый полиморфный подтип, который не апдейт** (вложение, кнопка, элемент
разметки): union-алиас генератор соберёт сам из `discriminator.mapping`, а
регистрацию в retort нужно дописать руками - иначе adaptix не загрузит и не
выгрузит тип, а упадёт `LoadError` уже в рантайме.

| Файл                              | Что                                              | Как падает пропуск            |
|-----------------------------------|--------------------------------------------------|-------------------------------|
| `src/maxo/serialization.py`       | `has_tag_provider(...)` в свою секцию `TAG_PROVIDERS` | тихо: `LoadError` в рантайме |
| `src/maxo/bot/warming_up.py`      | тип в кортеж `_types`                            | тихо: медленный первый запрос |

Свойство-дискриминатор бери из `discriminator.propertyName` базы в
`max-swagger.json`, а не по аналогии с соседями:

| Семейство          | База                | Свойство        | Enum                    |
|--------------------|---------------------|-----------------|-------------------------|
| Апдейты            | `Update`            | `"update_type"` | `UpdateType`            |
| Вложения           | `Attachment`        | `"type"`        | `AttachmentType`        |
| Вложения в запросе | `AttachmentRequest` | `"type"`        | `AttachmentRequestType` |
| Элементы разметки  | `MarkupElement`     | `"type"`        | `MarkupElementType`     |
| Кнопки             | `Button`            | `"type"`        | `ButtonType`            |

У апдейтов на проводе `update_type`, хотя поле класса называется `type`
(`ClassVar` в `MaxUpdate`) - это и есть причина сверяться со спекой.

Новое вложение тянет ещё ручной хвост: `factory()` и `to_request()` у типа и
его пары `*Request`, свойство-хелпер и ветка `attachment_type` в `MessageBody`,
а при заливке файлов через `UploadType` - запись в
`MEDIA_ATTACHMENT_FACTORIES` в `routing/mixins/attachments.py`.

**Новый метод Bot API:** `bind_method(...)` в `src/maxo/bot/bot.py` в блок
своего тега (без него метод недоступен с `Bot` и выглядит как
«не сгенерировался»); импорт и запись в `warming_up.py`; метод в фасад-миксин
`src/maxo/routing/mixins/` - только по правилу из шага 7.

**Новый член enum:** проверь `ENUM_EXTRAS` в `butcher/overrides.py`. Если член
был самодельным, а теперь есть в спеке - убери его из `ENUM_EXTRAS`, иначе в
классе окажутся два одинаковых имени и `StrEnum` бросит
`TypeError: 'X' already defined` прямо на импорте.

**Новое поле с `unsafe_*`:** само поле и свойство генерируются, но добавь
кейс в `tests/maxo/types/test_accessors.py` - там ручные списки defined/omitted.

**Метод или тип пропал из спеки:** удалить файл в `src/maxo`, вычистить
`bind_method`, `warming_up`, `serialization`, фасады, реестры и тесты; если
символ был публичным - оставить deprecated-алиас.

### 7. Правила по умолчанию

Решения, которые иначе переоткрываются каждый раз. Если мейнтейнер решит
иначе - поменяй правило здесь, а не рассуждай заново в следующий заход.

1. **Миксин в `CLASS_MIXINS`** выбирается по полям апдейта: есть `message` ->
   `MessageMethodsFacade`; есть `callback` -> `CallbackMethodsFacade`
   (и `MessageMethodsFacade` следом); иначе есть `chat_id` ->
   `ChatMethodsFacade`.
2. **Фасад заводится всегда**: `_FACADES_MAP` - единственный путь к
   `ctx["facade"]`. Поля апдейта выносятся в фасад целиком, как `@property`, по
   образцу ближайшего аналога.
3. **Фасад-миксин `routing/mixins/` - не зеркало Bot API.** Новый метод
   добавляется в миксин, только если у него там уже есть семья (парный метод
   того же семейства). Нет семьи - не добавляем.
4. **Депрекейтед-слои ведут себя по-разному.** `maxo.routing.updates`
   **пополняется**: новый апдейт идёт и в `__init__.py` шима, и отдельным
   deep-модулем `routing/updates/<name>.py`, и в `parametrize` в
   `tests/maxo/routing/updates/test_deprecation.py`. А `maxo.utils.facades`
   **заморожен**: новый фасад живёт только в `maxo.routing.facades`.
5. **Дрейф вне дельты не чиним.** Если генератор расходится с `src/maxo` в
   файле, которого изменение контракта не касалось (известный случай -
   `Chat.participants`), это отдельная задача и отдельный коммит.
6. **Ветка в `update_context.py`** выбирается по полям апдейта: message-scoped
   (есть `message`) или chat-scoped (есть `chat_id` и `user`).

### 8. Тесты, документация и примеры

- `docs/pages/botapi/types.rst`, `methods.rst`, `enums.rst`, `bot.rst` - это
  `automodule`, правки не требуют. **Но `docs/pages/botapi/updates.rst` - ручной
  список `autoclass`, а `docs/pages/event-handling/routers.rst` - ручная
  таблица событий.** `docs/pages/changelog.md` собирается из GitHub Releases,
  руками не трогать.
- Новый апдейт: тест полноты регистрации в `tests/maxo/routing/`. Если такого
  файла ещё нет - заведи, форма ниже. Он параметризован по `Updates` и
  автоматически ловит забытый observer и `_FACADES_MAP` для всех будущих
  апдейтов. `update_context.py`, docs и examples он не ловит - их проверяй
  глазами по карте касаний.
- Новый метод: тест wire-контракта и дампа рядом с `tests/maxo/bot/methods`.
- Новое поле: кейс в `tests/maxo/types/test_accessors.py`.

### 9. Проверить, что перенос точный

Жёсткая проверка вместо «вроде перенёс правильно»:

```bash
just butcher --output-dir .butcher/check

count_generated_diff() {
    generated_diff_exit=0
    generated_diff=$(diff -rq --exclude=__pycache__ "$1" "$2") ||
        generated_diff_exit=$?
    if [ "$generated_diff_exit" -gt 1 ]; then
        return "$generated_diff_exit"
    fi
    printf "%s\n" "$generated_diff" |
        awk 'NF { count++ } END { print count + 0 }'
}

count_generated_diff src/maxo/types .butcher/check/types
count_generated_diff src/maxo/enums .butcher/check/enums
count_generated_diff src/maxo/bot/methods .butcher/check/bot/methods
```

Функция считает все расхождения, включая `Only in`. Пустой diff печатает `0`
и завершается успешно; настоящая ошибка `diff` остаётся ошибкой даже с
`set -e` и `pipefail`.

Расходиться должны **только** файлы ручного слоя, и их набор обязан совпасть с
тем, что был до изменения контракта. Ориентир на момент написания: 33 типа,
0 enum'ов, 13 методов = 46 файлов. Появился 47-й - ты перенёс дельту неточно;
пропал - затёр ручной слой.

### 10. Проверки и уборка

```bash
PYTHONPATH=src uv run python -c "import maxo"
uv run mypy --config-file pyproject.toml
uv run ruff check --no-fix .
uv run codespell src examples
PYTHONPATH=src uv run slotscheck -m maxo
uv run bandit -c pyproject.toml src -r
just test
just butcher-test   # если трогал butcher/
rm -rf .butcher
```

`import maxo` запускай **первым**: он падает громко и дёшево, а `mypy` на
сломанном дереве выдаёт сотни бессмысленных ошибок.

Линтеры гоняй именно так, а не через `just lint`: рецепт `just ruff` - это
`ruff check --fix .`, он чинит найденное и зеленеет. Того же требует корневой
`AGENTS.md`.

## Сниппеты для тестов

Новый апдейт - полнота регистрации плюс путь «сырой JSON -> retort -> тип»:

```python
import typing
from typing import Any

import pytest

from maxo import Router
from maxo.routing.facades.middleware import _FACADES_MAP
from maxo.serialization import create_retort
from maxo.types import Updates

UPDATE_TYPES: tuple[Any, ...] = typing.get_args(Updates)


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_has_observer(update_tp: Any) -> None:
    assert update_tp in Router().observers


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_has_facade(update_tp: Any) -> None:
    assert update_tp in _FACADES_MAP


def test_new_update_loads_from_raw_json() -> None:
    retort = create_retort(warming_up=False)
    raw = {"update_type": "...", "timestamp": 1730000000000}  # + поля апдейта

    update = retort.load(raw, Updates)

    assert isinstance(update, ...)
```

Новый метод - wire-контракт и форма дампа. Тип результата достаётся через
`__orig_bases__`: атрибута `__result_type__` не существует, а прямой доступ
ловит `mypy` как `attr-defined`.

```python
import typing

from maxo.serialization import create_retort


def test_wire_contract() -> None:
    assert NewMethod.__url__ == "chats/{chat_id}/pins"
    assert NewMethod.__method__ == "get"
    # __orig_bases__ не описан в стабах, отсюда getattr вместо прямого доступа.
    orig_bases = getattr(NewMethod, "__orig_bases__")  # noqa: B009
    assert typing.get_args(orig_bases[0]) == (ExpectedResult,)


def test_dump() -> None:
    retort = create_retort(warming_up=False)

    assert retort.dump(NewMethod(chat_id=-42, count=10)) == {
        "path": {"chat_id": -42},
        "query": {"count": 10},
    }
```

## Повторяешь одну и ту же правку - правь таблицу, а не `src/maxo`

Главное правило butcher. Симптом -> куда класть (всё в `butcher/overrides.py`):

| Симптом после генерации                                     | Таблица                                          |
|-------------------------------------------------------------|--------------------------------------------------|
| Схема/операция/enum вообще не нужны в maxo                   | `SKIP_SCHEMAS` / `SKIP_OPERATIONS` / `SKIP_ENUMS` |
| Тип поля метода вышел `Any` из-за кривой спеки               | `METHOD_FIELD_TYPES`                             |
| Тип или обязательность поля модели надо поправить            | `MODEL_FIELD_OVERRIDES` (`FieldOverride`)        |
| Нужен член enum, которого нет в спеке, или алиас под aiogram | `ENUM_EXTRAS`                                    |
| Нужен фасад в базах класса                                   | `CLASS_MIXINS`                                   |
| Нужен алиас-тип уровня модуля                                | `TYPE_ALIASES`                                   |
| Ручной символ должен попасть в сгенерированный `__init__.py` | `TYPES_EXTRA_EXPORTS` / `METHODS_EXTRA_EXPORTS`  |
| Состав union-файла или замена ссылки на базу                 | `UNION_FILES` / `BASE_TO_UNION`                  |
| База ведётся руками, а подтипы генерируются                  | `REPLACED_BASES`                                 |

Если проблема не в maxo-профиле, а в разборе OpenAPI - веди исправление в
upstream, не костыль в butcher. Обновление закреплённой PyPI-версии
генератора делай отдельным изменением.
Новую трансформацию профиля закрывай тестом в `butcher/tests/test_profile.py`,
новую форму вывода - в `butcher/tests/test_render.py`.

Отдельный случай - дефекты самой спеки, которые видны только в докстрингах
(незакрытые ```` ``` ````, забор из двух или четырёх бэктиков). Сейчас в
`max-swagger.json` их четыре: `editMyCommands`, `getAdmins`, `sendMessage`,
`getVideoAttachmentDetails`; в `src/maxo` они уже исправлены руками и любая
генерация возвращает их обратно. Чини такое **в `max-swagger.json`** - файл
уже правился так же (коммит `e5732c7`), и он единственный источник правды.

## Red flags - остановись

- «Просто запущу `just butcher` и посмотрю, что получилось» в грязном дереве.
  Дельту потом не отличить от ручного слоя.
- Блок импортов скопирован из снимка вслепую и после переноса не прогнан ruff.
- `git diff` после переноса дельты удаляет `factory`, `to_request`, `@property`
  или `# type: ignore` - ты стёр ручной слой.
- Шаг 9 даёт другое число расходящихся файлов, чем было до правки спеки.
- Новый апдейт добавлен в `types/`, но не тронуты `serialization.py`,
  `_FACADES_MAP` и `update_context.py` - всё три падают молча.
- Новый подтип уже появился в union-алиасе (`Attachments`, `InlineButtons`,
  `MarkupElements`), и кажется, что он зарегистрирован. Алиас собирает
  генератор из `discriminator.mapping`, а `TAG_PROVIDERS` - нет. Проверь.
- Пропущен шаг 5: ты полагаешься только на таблицу, а она отстаёт от кода.
- Одну и ту же правку в `src/maxo` делаешь второй раз - её место в
  `overrides.py` или в `max-swagger.json`.
- `just mypy` зелёный, а `import maxo` не проверял - дубли членов enum и циклы
  импортов mypy не ловит.

## Если всё-таки нужна полная перегенерация

Только когда менялся сам butcher и дельта затрагивает почти все файлы:

```bash
git status --porcelain   # обязано быть пусто
just butcher             # пишет прямо в src/maxo
git diff -- src/maxo     # это и есть список потерянного ручного слоя
```

Дальше вручную вернуть каждый удалённый ручной кусок по
`references/manual-layer.md` и прогнать все проверки. Если запутался -
`git checkout -- src/maxo` и вернись к процедуре с дельтой.
