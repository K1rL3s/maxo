# AGENTS.md - butcher, кодогенерация maxo

Дополняет корневой `AGENTS.md`. Butcher генерирует `src/maxo/types`,
`src/maxo/enums` и `src/maxo/bot/methods` из `max-swagger.json` и
`max-swagger.yaml` в корне - вместе они источник правды по контракту MAX Bot
API.

## Две публикации спеки

MAX публикует контракт дважды, у каждой публикации есть своё. Генерация идёт
по их объединению, поэтому обновляются обе.

| Файл               | Откуда                                                   | Только там                                                                              |
|--------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------------|
| `max-swagger.json` | `dev.max.ru/docs-api`, способом из `examples/swagger_watcher.py` | Русские описания, свежие методы и апдейты, права администратора, свёрнутые методы вроде `GET /chats` |
| `max-swagger.yaml` | Репозиторий `max-messenger/api-schema`                   | `nullable`, `deprecated`, `ChatStatus.suspended`, `mark_seen`, `view_stats`, `before`/`after` |

```bash
# yaml кладётся в корень целиком: ручного слоя в нём нет
gh api repos/max-messenger/api-schema/contents/schema.yaml \
  -H "Accept: application/vnd.github.raw" > max-swagger.yaml

# json с сайта - в сторону: в корневой файл переносится только дельта
uv run python - <<'PY'
import asyncio, json, sys
from pathlib import Path

sys.path.insert(0, "examples")
from aiohttp import ClientSession, ClientTimeout
from swagger_watcher import REQUEST_HEADERS, fetch_openapi


async def main() -> None:
    async with ClientSession(
        headers=REQUEST_HEADERS,
        timeout=ClientTimeout(total=60),
    ) as session:
        spec = await fetch_openapi(session)
    Path(".butcher/site-swagger.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=4) + "\n",
    )


asyncio.run(main())
PY
```

`.butcher/site-swagger.json` сравнивается с `max-swagger.json`, и в корневой
файл переносится только дельта сайта. Осознанные расхождения с сайтом
(исправленные markdown-заборы и curl-примеры, свёрнутые методы, оставленные
параметры, поля из yaml) перечислены в
`.agents/skills/butcher-update/references/manual-layer.md` и должны уцелеть.

`merge.py` накладывает yaml на json. База - json: описания, `required` и ручные
правки остаются его; из yaml добираются только отсутствующие в базе пути,
методы, схемы, свойства, параметры, члены enum и флаги `nullable`/`deprecated`.
Части `allOf` сопоставляются по порядку и только при равном их числе. Описания
в yaml английские, поэтому поле или параметр, пришедший только из yaml,
дописывается в `max-swagger.json` с русским описанием: текст возьмётся из json,
типы и флаги - из yaml.

## Запуск

```bash
just butcher --output-dir .butcher/gen   # вывод в сторону
just butcher-test
```

`--spec` задаёт основную спеку (путь или URL), `--extra-spec` - вторую
публикацию (по умолчанию `max-swagger.yaml`), `--extra-spec ""` отключает
слияние. Каталог `.butcher` в `.gitignore`.

**Генерацию всегда направляй в сторону через `--output-dir`.** Генератор
перезаписывает файлы целиком и стирает ручной слой. Прямой вывод в `src/maxo`
допустим только для полной перегенерации после изменения самого butcher: на
чистом дереве, с восстановлением каждого фрагмента из `manual-layer.md` и
полным прогоном проверок.

## Устройство

Разбор свагера (`allOf`, `oneOf`/`anyOf`, `nullable` в форме 3.0 и 3.1,
форматы, дефолты, `readOnly`, дискриминаторы, тела запросов, внешние `$ref`,
коллизии имён) делает PyPI-пакет `unihttp-openapi-generator` из dependency
group `butcher`: он строит IR. За butcher - только отличия maxo от свагера.

```text
max-swagger.json + max-swagger.yaml
  -> merge.merge_specs()      объединение публикаций
  -> spec.load()              build_ir генератора
  -> profile.build_profile()  maxo-трансформации IR в Model/Enum/Unions/Method
  -> render/*                 стиль вывода maxo
  -> emit.write()             запись + ruff конфигом проекта
```

`naming.py` - имена классов и пути модулей, `__main__.py` - CLI, `tests/` -
тесты профиля, рендера и слияния на маленькой фикстуре-спеке.

IR строится с двумя обязательными флагами (`spec.py`):

- `inheritance=True` - поля родителя остаются у родителя. Без него
  `PhotoAttachment` получил бы копию полей `Attachment`, а база стала бы
  union-алиасом.
- `omit_optionals=True` - необязательное поле - `Omittable[...] = Omitted()`,
  а не `T | None = None`. Дефолты свагера у полей моделей и методов
  игнорируются.

Docstring'и (`render/docs.py`) печатаются как в спеке, кроме:

- `<br/>`, `<br>`, `</br>` становятся переносом строки.
- `collapse_list_blanks` убирает пустые строки перед пунктами списка (везде,
  включая методы; ``` не трогает).
- `reflow_lists` сдвигает плотный список за вводной на +4 - только у типов и
  enum'ов, у методов списки перемешаны с curl-примерами.
- Поле без описания, чей тип - алиас из `INLINE_ALIASES`, берёт описание
  алиаса (`Subscribe.url` -> `SubscriptionUrl`).
- Параметр с `deprecated` получает в описании абзац `_Устаревший параметр_`
  (`spec.mark_deprecated_parameters`): IR генератора флаг у параметров не
  переносит.
- `unsafe_*`-свойства идут по алфавиту имени поля.

## Оверрайды

Всё, чем maxo намеренно отличается от свагера, - данные в `overrides.py`;
логика - в `profile.py`, без зашитых имён схем. **Если после генерации файл
приходится править руками одинаковым образом, правь таблицу, а не
`src/maxo`.**

- `SKIP_SCHEMAS` / `SKIP_ENUMS` / `SKIP_OPERATIONS` - не генерировать. Пропуск
  базы каскадом уносит наследников.
- `REPLACED_BASES` - файл схемы не генерируется, подтипы остаются (`Update` ->
  ручной `MaxUpdate`), без каскада.
- `MODEL_BASE_OVERRIDES` - база, которой maxo уточняет плоскую схему
  (`CommentMessage` -> `Message`).
- `UNION_FILES` + `BASE_TO_UNION` - состав `attachments.py`, `buttons.py`,
  `markup_elements.py`, `updates.py` и замена ссылки на базу в аннотациях.
- `ENUM_EXTRAS` - самодельные члены enum и aiogram-алиасы
  (`AttachmentType.TEXT`, `ChatType.PRIVATE`, `ParseMode`, `ContentType`).
  Член, который есть хотя бы в одной публикации, сюда не пиши: будет дубль.
- `TYPE_ALIASES` - алиасы уровня модуля (`CallbackQuery = MessageCallback`).
- `CLASS_MIXINS` - фасады в базах классов; `FACADE_MODULES` - модуль каждого
  фасада, из которого butcher генерирует импорт.
- `TYPES_EXTRA_EXPORTS` / `METHODS_EXTRA_EXPORTS` - ручные символы в
  сгенерированных `__init__.py`.
- `INLINE_ALIASES`, `TIMESTAMP_HINTS` - скаляры, встраиваемые как тип, и слова,
  по которым int64 считается таймстемпом.
- `METHOD_FIELD_TYPES` - тип поля метода по `(класс, поле)`, где свагер описан
  неверно и генератор выводит `Any` (`GetMessages.message_ids` - массив без
  `items`).
- `METHOD_FIELD_DESCRIPTIONS` - описание поля метода, когда одна wire-модель
  служит операциям с разной семантикой.
- `MODEL_FIELD_OVERRIDES` (`FieldOverride`) - поле модели по `(класс, поле)`:
  тип, принудительный `Omittable`, хвостовой комментарий. Ссылку на другую
  схему меняет `ref=...`, а не только `annotation`; `ref` сохраняет
  `nullable` поля, `annotation` заменяет тип целиком.
- `DEPRECATED_METHODS` - сгенерированный метод, который MAX убрал, и текст
  предупреждения: класс получает `@deprecated(..., stacklevel=2)`. Сайт
  сообщает об удалении только прозой и вендорским полем
  `disable-notification`, флага `deprecated` у операций нет ни в одной
  публикации. Ручной устаревший метод помечается `ExtraExport(...,
  deprecated=True)`. Импорт устаревших методов в `maxo/bot/methods/__init__.py`
  butcher пишет с `# type: ignore[deprecated]`.

## Ручной слой

Butcher не знает ручных файлов, методов вне свагера, `factory()`/`to_request()`,
aiogram-алиасов, сужений с `# type: ignore` и полей вне спеки, и стирает их
при генерации поверх. Полный перечень и зависимости - в
`.agents/skills/butcher-update/references/manual-layer.md`; держи его
актуальным. Без алиасов-свойств после генерации падает `just mypy`, без
`factory()` - уже `import maxo`.

## Обновление контракта

Переносится только дельта между генерациями по старой и новой спекам.

1. `git status --porcelain -- src/maxo/types src/maxo/enums src/maxo/bot/methods`
   пуст.
2. Скачай обе публикации, обнови `max-swagger.yaml` целиком, в
   `max-swagger.json` перенеси дельту сайта.
3. Снимок по старым спекам - до любых правок `overrides.py`: оверрайд
   применяется к каждому снимку, где есть его класс, и правка существующего
   класса, попавшая в оба снимка, выпадет из дельты.

   ```bash
   mkdir -p .butcher
   git show HEAD:max-swagger.json > .butcher/spec-before.json
   git show HEAD:max-swagger.yaml > .butcher/spec-before.yaml
   just butcher --spec .butcher/spec-before.json \
     --extra-spec .butcher/spec-before.yaml --output-dir .butcher/before
   ```

   Затем нужные оверрайды (`CLASS_MIXINS` для нового апдейта,
   `MODEL_BASE_OVERRIDES` для новой базы) и снимок по новым спекам:

   ```bash
   just butcher --output-dir .butcher/after
   diff -ru .butcher/before .butcher/after
   ```

   Оверрайд, добавленный после `after`, требует перегенерации `after` и
   повторного переноса затронутого типа.
4. Перенеси дельту в `src/maxo`: новый файл - целиком, изменённый - по ханкам
   (`patch -p2 -d src/maxo` по выводу `diff -ru` работает, но проверь
   `.orig`/`.rej`), исчезнувший - удали, проверив использование символа в
   `src/`, `tests/`, `docs/`, `examples/` и `butcher/`.
5. Сверь дерево с новым снимком:

   ```bash
   just butcher --output-dir .butcher/check
   diff -rq src/maxo/types .butcher/check/types
   diff -rq src/maxo/enums .butcher/check/enums
   diff -rq src/maxo/bot/methods .butcher/check/bot/methods
   ```

   Набор расхождений, включая `Only in`, совпадает с набором до обновления плюс
   осознанный новый ручной слой. Дрейф, где генератор точнее дерева
   (`Chat.participants`), в рамках обновления не чинится.
6. `just butcher-test` (если менялся `butcher/`), `just lint`, `just mypy`,
   `just test`, `PYTHONPATH=src uv run python -c "import maxo"` (ловит циклы
   импортов).

Ruff в прогоне в сторону ставит импорт ещё не существующего в `src/maxo` типа
в отдельную third-party группу: isort считает модуль first-party, только если
он есть на диске (`src = ["src", "examples", "tests"]`). Блок импортов не
копируй вслепую, а по затронутым файлам прогоняй `uv run ruff check --fix`.

## Новый тип апдейта

Генерация даёт только `maxo/types/<name>.py` и запись в union `Updates`.
Остальное - руками, и большинство пропусков падает молча:

- `overrides.CLASS_MIXINS` - фасад по полям апдейта: `message` ->
  `MessageMethodsFacade`, `callback` -> `CallbackMethodsFacade`, иначе
  `chat_id` -> `ChatMethodsFacade`.
- `serialization.py` - `has_tag_provider(X, "update_type", UpdateType.X)`, без
  него `LoadError` в рантайме.
- `routing/routers/simple.py` - `UpdateObserver[X]()` и запись в `_observers`.
- `routing/middlewares/update_context.py` - ветка `isinstance` для
  `chat_id`/`user`/`user_id`, иначе тихо ломаются ключи FSM, диалоги и фильтры.
- `bot/warming_up.py` - тип в `_types`.
- `docs/pages/botapi/updates.rst` (`autoclass`),
  `docs/pages/event-handling/routers.rst` (таблица событий),
  `examples/all_updates.py`.

## Новый полиморфный подтип

Union-алиас собирается из `discriminator.mapping` сам, регистрация в retort -
ручная: без неё подтип есть в аннотациях, но не грузится и не выгружается, и
тесты этого не ловят. Подтип дописывается в `TAG_PROVIDERS` в
`src/maxo/serialization.py`, в свою секцию `# ---> ... <---`:

| Семейство          | База                | Свойство на проводе | Enum                    |
|--------------------|---------------------|---------------------|-------------------------|
| Апдейты            | `Update`            | `"update_type"`     | `UpdateType`            |
| Вложения           | `Attachment`        | `"type"`            | `AttachmentType`        |
| Вложения в запросе | `AttachmentRequest` | `"type"`            | `AttachmentRequestType` |
| Элементы разметки  | `MarkupElement`     | `"type"`            | `MarkupElementType`     |
| Кнопки             | `Button`            | `"type"`            | `ButtonType`            |

Свойство бери из `discriminator.propertyName` базы в спеке: у апдейтов на
проводе `update_type`, хотя в классе это `type` (`ClassVar` в `MaxUpdate`).

Ещё тип в `_types` в `bot/warming_up.py`. Новому вложению дополнительно нужны
`factory()` и `to_request()` у него и у пары `*Request`, свойство-хелпер и
ветка `attachment_type` в `MessageBody`, а заливаемому через `UploadType` -
запись в `MEDIA_ATTACHMENT_FACTORIES` в `types/facades/attachments.py`.

## Разработка butcher

- Ошибку самого генератора исправляй в upstream, а не костылём в butcher;
  подъём закреплённой версии - отдельным изменением.
- Butcher вне `mypy`, но под `ruff` с конфигом проекта.
- Тесты butcher вне автосбора `pytest` (`testpaths = ["tests"]`), запуск -
  `just butcher-test`. Трансформация профиля закрывается тестом в
  `tests/test_profile.py`, форма вывода - в `tests/test_render.py`. Фикстура в
  `tests/conftest.py` намеренно урезана: профиль переживает спеку без части
  схем из таблиц оверрайдов.
