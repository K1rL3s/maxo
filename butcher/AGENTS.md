# AGENTS.md - butcher, кодогенерация maxo

Правила для AI-агентов, работающих с `butcher/`. Дополняет корневой
`AGENTS.md`, а не заменяет его: общие правила проекта (русский язык, короткое
тире, строгая типизация, conventional commits) действуют и здесь.

Butcher генерирует `src/maxo/types`, `src/maxo/enums` и `src/maxo/bot/methods`
из `max-swagger.json` в корне репозитория. Этот файл - единственный источник
правды по контракту MAX Bot API.

## Команды

```bash
just butcher       # полная генерация в src/maxo, только по правилу ниже
just butcher-test  # тесты butcher
```

`just butcher` принимает аргументы CLI, например
`just butcher --output-dir /tmp/maxo-gen` - удобно, чтобы посмотреть вывод, не
трогая рабочее дерево, или `--spec <путь или URL>` для другой спеки.

**Не начинай обновление контракта с `just butcher` без `--output-dir`.**
Генератор перезаписывает файлы целиком и стирает ручной слой. Прямой вывод в
`src/maxo` допустим только для полной перегенерации после изменения самого
butcher, на чистом дереве и с последующим восстановлением каждого ручного
фрагмента.

## Как это устроено

Butcher **не разбирает свагер сам**. За `allOf`, `oneOf`/`anyOf`, `nullable` в
обеих формах (3.0 `nullable: true` и 3.1 `type: [x, "null"]`), форматы,
дефолты, `readOnly`, дискриминаторы, тела запросов, внешние `$ref` и коллизии
имён отвечает PyPI-пакет `unihttp-openapi-generator==0.3.1` из dependency
group `butcher`. `uv sync --all-groups` устанавливает его вместе с остальным
окружением. Пакет строит IR - типизированное промежуточное представление,
независимое от того, во что потом рендерится код.

За butcher остаётся только то, чем maxo отличается от голого свагера.

```text
max-swagger.json
  -> spec.load()            загрузка + build_ir (генератор)
  -> profile.build_profile()  maxo-трансформации IR
  -> render/*                 стиль вывода maxo
  -> emit.write()             запись в src/maxo + ruff
```

| Модуль          | Назначение                                                                 |
|-----------------|----------------------------------------------------------------------------|
| `spec.py`       | Загрузка спеки и построение IR. Здесь же выбираются флаги генератора.       |
| `profile.py`    | Трансформации IR в структуры `Model`/`Enum`/`Unions`/`Method`.              |
| `overrides.py`  | Декларативные таблицы отличий maxo от свагера. Только данные, без логики.   |
| `naming.py`     | Имена классов и пути модулей внутри пакета `maxo`.                          |
| `render/`       | Печать кода: типы, enum'ы, union-файлы, методы, `__init__.py`, docstring'и. |
| `emit.py`       | Запись файлов и форматирование через `ruff` (конфигом проекта).             |
| `__main__.py`   | CLI на argparse.                                                            |
| `tests/`        | Тесты профиля и рендера на маленькой фикстуре-спеке.                        |

### Флаги генератора

IR строится с двумя обязательными для maxo флагами (`spec.py`):

- `inheritance=True` - поля родителя остаются у родителя, подтипы наследуются.
  Без него `PhotoAttachment` получил бы копию полей `Attachment`, а сама база
  превратилась бы в union-алиас.
- `omit_optionals=True` - необязательные поля остаются
  `Omittable[...] = Omitted()`, а не схлопываются в `T | None = None`.

### Docstring'и типов и enum'ов

`render/docs.py` печатает описания «как есть», но приводит к порядку списки:

- `<br/>` (и `<br>`, `</br>`) разворачиваются в перенос строки.
- `collapse_list_blanks` убирает пустые строки **перед пунктами** списка -
  печатаем списки плотно за вводной. ``` не трогаем. Работает для всех
  docstring'ов, включая методы.
- `reflow_lists` сдвигает пункты плотного списка на +4, если список идёт
  вплотную за вводной (отступ решается по первому пункту и держится на весь
  список). Только для типов и enum'ов (`reflow=True`); у методов списки и
  curl-примеры вперемешку.

`unsafe_*`-свойства печатаются по алфавиту имени поля.

Дефолты свагера у полей моделей игнорируются, как и у методов: `required:
false` - это `Omittable[...] = Omitted()`, а не `= <default>`.

## Слой оверрайдов

`overrides.py` - место для всего, чем maxo намеренно отличается от свагера:

- `SKIP_SCHEMAS` / `SKIP_ENUMS` / `SKIP_OPERATIONS` - что не генерировать.
  Пропуск базы каскадом уносит всех её наследников.
- `REPLACED_BASES` - схема, чей файл не генерируется, но подтипы остаются
  (`Update` -> ручной `MaxUpdate`). Каскада, в отличие от `SKIP_SCHEMAS`, нет.
- `UNION_FILES` + `BASE_TO_UNION` - состав `attachments.py`, `buttons.py`,
  `markup_elements.py`, `updates.py` и чем заменяется ссылка на базу в
  аннотациях полей.
- `ENUM_EXTRAS` - самодельные члены enum'ов и aiogram-алиасы
  (`AttachmentType.TEXT`, `SenderAction.MARK_SEEN`, `ParseMode`, `ContentType`).
- `TYPE_ALIASES` - алиасы уровня модуля внутри сгенерированного типа
  (`CallbackQuery = MessageCallback`).
- `CLASS_MIXINS` - фасады в базах классов (`MessageMethodsFacade` и другие).
- `TYPES_EXTRA_EXPORTS` / `METHODS_EXTRA_EXPORTS` - ручные символы, которые
  должны попасть в сгенерированные `__init__.py`.
- `INLINE_ALIASES`, `TIMESTAMP_HINTS` - мелкие правила типов.
- `METHOD_FIELD_TYPES` - точечная замена типа поля метода по
  `(класс, поле)` там, где свагер описан неверно и генератор выводит `Any`
  (например, тело `UserIdsList` записано как parameters-объект -> `user_ids`;
  `GetMessages.message_ids` - массив без `items`).
- `MODEL_FIELD_OVERRIDES` (`FieldOverride`) - правки полей моделей по
  `(класс, поле)`: заменить тип, форсировать `Omittable` и добавить хвостовой
  комментарий. Так генерируются `MessageButton.text` (сужение до `Omittable` с
  `# type: ignore`) и `PhotoAttachmentRequestPayload.photos` (map в свагере, но
  на деле список).

**Главное правило: если после генерации приходится править файл руками
одинаковым образом - правь таблицу в `overrides.py`, а не `src/maxo`.**

## Что остаётся ручным

Butcher не создаёт и при генерации затрёт, если файл лежит на его пути:

- `src/maxo/types/base.py` (`MaxoType`, `MaxUpdate`, `BaseMethodsFacade`).
- `factory()` и `to_request()` у attachment-типов, `generated_url` у
  `Message`, `keyboard`/`content_type` у `MessageBody` и подобные хелперы.
- Методы вне свагера: `GetChatByLink`, `DeleteChat`, `UploadMedia`,
  `EditBotInfo`, `GetChats`, `SetAdmins`.
- Кастомные хвосты методов: `GetUpdates.make_response`,
  `UploadMedia.validate_response`.
- `serialization.py` (`TAG_PROVIDERS`) и `warming_up.py` - butcher их не
  трогает, но при новом полиморфном типе их нужно обновить руками.
- Поля, которых нет в свагере: `Chat.chat_message_id` вместе с
  `unsafe_chat_message_id`. Butcher их не знает и вычистит.
- Алиасы-свойства и сужения типов с `# type: ignore[assignment]`:
  `Message.message`, `Chat.id`, `User.id`/`fullname`, `Callback.id`/`data`,
  `MessageCallback.message`. Без них `just mypy` после генерации падает -
  восстанавливай их вместе с остальным ручным кодом. (`MessageButton.text`
  теперь генерируется через `MODEL_FIELD_OVERRIDES`.)

### Безопасное обновление контракта

Обычное обновление переносит дельту между двумя генерациями:

1. Убедись, что `git status --porcelain -- src/maxo` пуст.
2. Возьми старую спецификацию через `git show HEAD:max-swagger.json`, сгенерируй
   её в `.butcher/before`.
3. Обнови `max-swagger.json`. Для нового апдейта добавь запись в
   `overrides.CLASS_MIXINS` **до** генерации следующего снимка.
4. Сгенерируй новую спецификацию в `.butcher/after` и получи дельту через
   `diff -ru .butcher/before .butcher/after`.
5. Перенеси только эту дельту в `src/maxo`, не удаляя ручной слой. Новый файл
   можно скопировать целиком, изменённый файл правится по ханкам, исчезнувший
   файл удаляется.
6. Снова сгенерируй результат в `.butcher/check` и сравни его с тремя
   сгенерированными каталогами в `src/maxo`. Учитывай все строки `diff -rq`,
   включая `Only in`; набор расхождений должен отличаться от исходного только
   новым осознанным ручным слоем.

Если `CLASS_MIXINS` добавлен после создания `.butcher/after`, повтори генерацию
этого снимка и заново перенеси затронутый тип. Иначе класс в `src/maxo`
останется без фасад-миксина.

### Новый тип апдейта: ручная регистрация

Генерация даёт только `maxo/types/<name>.py` и запись в union `Updates`. Всё
остальное - руками, и большая часть пропусков падает молча:

- `serialization.py` - `has_tag_provider(X, "update_type", UpdateType.X)`.
  Забыл - `LoadError` в рантайме.
- `routing/routers/simple.py` - `UpdateObserver[X]()` и запись в `_observers`.
  Забыл - хендлер некуда зарегистрировать.
- `routing/middlewares/update_context.py` - ветка `isinstance`, заполняющая
  `chat_id`/`user`/`user_id`. Забыл - тихо ломаются ключи FSM, диалоги и фильтры.
- `overrides.CLASS_MIXINS` - миксин-фасад по полям апдейта: есть `message` ->
  `MessageMethodsFacade`, есть `callback` -> `CallbackMethodsFacade`, иначе
  есть `chat_id` -> `ChatMethodsFacade`.
- `bot/warming_up.py` - тип в списке типов.
- `docs/pages/botapi/updates.rst` (ручной список `autoclass`),
  `docs/pages/event-handling/routers.rst` (таблица событий),
  `examples/all_updates.py`.

`collect_used_updates` правок не требует - он обходит `observers` динамически.

### Новый полиморфный тип: `TAG_PROVIDERS`

Union-алиас (`Attachments`, `InlineButtons`, `MarkupElements`, `Updates`)
собирается генератором из `discriminator.mapping` сам, а вот регистрация в
retort - ручная. Без неё подтип есть в аннотациях, но adaptix не умеет его ни
загрузить, ни выгрузить: `LoadError` в рантайме, тесты этого не ловят.

Новый подтип дописывается в `TAG_PROVIDERS` в `src/maxo/serialization.py`, в
свою секцию (они помечены комментариями `# ---> ... <---`):

| Семейство            | База                | Свойство на проводе | Enum                    |
|----------------------|---------------------|---------------------|-------------------------|
| Апдейты              | `Update`            | `"update_type"`     | `UpdateType`            |
| Вложения             | `Attachment`        | `"type"`            | `AttachmentType`        |
| Вложения в запросе   | `AttachmentRequest` | `"type"`            | `AttachmentRequestType` |
| Элементы разметки    | `MarkupElement`     | `"type"`            | `MarkupElementType`     |
| Кнопки               | `Button`            | `"type"`            | `ButtonType`            |

```python
has_tag_provider(NewAttachment, "type", AttachmentType.NEW)
```

Свойство берётся из `discriminator.propertyName` базы в `max-swagger.json`, а
не по аналогии: у апдейтов на проводе `update_type`, хотя в классе поле
называется `type` (`ClassVar` в `MaxUpdate`). Появится новая дискриминированная
база - свойство смотри в спеке.

Дальше по тому же подтипу:

- `bot/warming_up.py` - тип в кортеж `_types`.
- Для нового вложения ещё ручной хвост: `factory()` и `to_request()` у самого
  типа и его пары `*Request`, свойство-хелпер и ветка `attachment_type` в
  `MessageBody`, а если файл заливается через `UploadType` - запись в
  `MEDIA_ATTACHMENT_FACTORIES` в `routing/mixins/attachments.py`.

## Правила разработки

- Логика - в `profile.py`, данные - в `overrides.py`. Не зашивай конкретные
  имена схем в код профиля.
- Если проблема в самом генераторе - оформляй исправление в upstream, а не
  обходи её костылём в butcher. Обновление закреплённой PyPI-версии делай
  отдельным изменением. Так уже сделаны `--inheritance`,
  `IRBodyField.description` и отказ от суффикса у soft keywords.
- Butcher не входит в `mypy` (`files` в `pyproject.toml`), но проверяется
  `ruff` с конфигом проекта.
- Тесты butcher не попадают в автосбор `pytest` (`testpaths = ["tests"]`) и
  запускаются только через `just butcher-test`. Им нужен установленный
  генератор.
- Новую трансформацию профиля закрывай тестом в `tests/test_profile.py`, новую
  форму вывода - в `tests/test_render.py`. Фикстура-спека живёт в
  `tests/conftest.py` и намеренно урезана: профиль должен переживать спеку, в
  которой нет части схем из таблиц оверрайдов.

## Проверка результата

1. Прогоны `before`, `after` и `check` по безопасной процедуре выше. Каталог
   `.butcher` уже в `.gitignore`.
2. `just butcher-test`.
3. После переноса дельты в `src/maxo`: `just lint`, `just mypy`, `just test` и
   `PYTHONPATH=src uv run python -c "import maxo"` (ловит циклы импортов).

### Импорты в прогоне «в сторону»

`emit.write` в конце гоняет по каталогу вывода `ruff check --select I,F401
--fix` и `ruff format` (`postprocess.format_path` в PyPI-пакете). Путь к конфигу
проекта передаётся явно, поэтому одинаково форматируется любой каталог вывода -
и `.butcher/gen`, и путь вне репозитория, и gitignore этому не мешает.

Одно исключение стоит знать, иначе оно съедает время на ровном месте. В
`pyproject.toml` задан `src = ["src", "examples", "tests"]`, и isort считает
модуль first-party, **только если он существует на диске**. Пока нового типа
нет в `src/maxo/types/`, ruff относит его к third-party и кладёт импорт в
отдельную группу:

```python
from typing import TypeAlias

from maxo.types.message_pinned import MessagePinned   # ещё нет файла в src/maxo

from maxo.types.bot_added_to_chat import BotAddedToChat
```

Это артефакт прогона в сторону, а не поломка генератора: ruff не сливает группы,
разделённые пустой строкой, поэтому повторный запуск в том же каталоге ничего не
изменит. Как только файл нового типа лёг в `src/maxo/types/`, генерация даёт
правильную единую группу. Поэтому при переносе кусков из прогона в сторону не
копируй блок импортов вслепую и в конце прогоняй `uv run ruff check --fix` по
затронутым файлам; последнее слово - за `uv run ruff check --no-fix .`.
