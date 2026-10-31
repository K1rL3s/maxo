---
name: butcher-update
description: Используется при изменении контракта MAX Bot API в maxo: обновлении max-swagger.json или max-swagger.yaml, новом или изменённом типе, enum, методе, update либо регенерации src/maxo/types, src/maxo/enums, src/maxo/bot/methods
---

# Обновление MAX Bot API через butcher

Генератор перезаписывает файлы целиком и стирает ручной слой (перечень -
`references/manual-layer.md`). Поэтому **генерация всегда идёт в сторону через
`--output-dir`**, а в `src/maxo` переносится только дельта двух снимков.
Устройство генератора и таблиц `butcher/overrides.py` - в `butcher/AGENTS.md`.

## Две публикации спеки

Генерация идёт по объединению, поэтому обновляются обе.

| Файл               | Откуда                                          | Только там                                                                     |
|--------------------|-------------------------------------------------|--------------------------------------------------------------------------------|
| `max-swagger.json` | `dev.max.ru/docs-api` (`examples/swagger_watcher.py`) | Русские описания, свежие методы и апдейты, права администратора, `GET /chats` |
| `max-swagger.yaml` | репозиторий `max-messenger/api-schema`          | `nullable`, `deprecated`, `ChatStatus.suspended`, `mark_seen`, `view_stats`, `before`/`after` |

```bash
# yaml - целиком: ручного слоя в нём нет
gh api repos/max-messenger/api-schema/contents/schema.yaml \
  -H "Accept: application/vnd.github.raw" > max-swagger.yaml

# json с сайта - в сторону, в корневой файл переносится только дельта
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

Осознанные расхождения `max-swagger.json` с сайтом (исправленные
markdown-заборы и curl-примеры, свёрнутые методы, оставленные параметры, поля
из yaml) перечислены в `references/manual-layer.md` и должны уцелеть. Поле или
параметр, пришедший только из yaml, дописывай в `max-swagger.json` с русским
описанием: при слиянии текст берётся из json, типы и флаги - из yaml.

## Процедура

1. `git status --porcelain -- src/maxo/types src/maxo/enums src/maxo/bot/methods`
   пуст.
2. Скачай обе публикации, обнови `max-swagger.yaml` целиком, в
   `max-swagger.json` перенеси дельту сайта.
3. Снимок по старым спекам - **до** правок `butcher/overrides.py`: оверрайд
   применяется к каждому снимку, где есть его класс, и правка существующего
   класса выпадет из дельты.

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

   Оверрайд, добавленный после `after`, требует перегенерации `after`.
4. Перенеси дельту в `src/maxo`: новый файл - целиком, изменённый - по ханкам
   (`patch -p2 -d src/maxo` по выводу `diff -ru`, проверь `.orig`/`.rej`),
   исчезнувший - удали, проверив символ в `src/`, `tests/`, `docs/`,
   `examples/`, `butcher/`. Блок импортов не копируй вслепую: в прогоне в
   сторону ruff кладёт ещё не существующий модуль в third-party группу, поэтому
   по затронутым файлам прогони `uv run ruff check --fix`.
5. Сверь дерево с новым снимком:

   ```bash
   just butcher --output-dir .butcher/check
   diff -rq src/maxo/types .butcher/check/types
   diff -rq src/maxo/enums .butcher/check/enums
   diff -rq src/maxo/bot/methods .butcher/check/bot/methods
   ```

   Набор расхождений (включая `Only in`) равен набору до обновления плюс
   осознанный новый ручной слой. Дрейф, где генератор точнее дерева
   (`Chat.participants`), в рамках обновления не чини.
6. `just lint`, `just mypy`, `just test`,
   `PYTHONPATH=src uv run python -c "import maxo"` (ловит циклы импортов);
   `just butcher-test`, если менялся `butcher/`.

## Новый тип апдейта

Генерация даёт только `maxo/types/<name>.py` и запись в union `Updates`.
Остальное - руками, и большинство пропусков падает молча:

1. `overrides.CLASS_MIXINS` - фасад по полям: `message` ->
   `MessageMethodsFacade`, `callback` -> `CallbackMethodsFacade`, иначе
   `chat_id` -> `ChatMethodsFacade`.
2. `src/maxo/serialization.py` - запись в `_UPDATE_TAGS`, иначе `LoadError`.
3. `src/maxo/routing/routers/simple.py` - `UpdateObserver[X]()` и запись в
   `_observers`.
4. `src/maxo/routing/middlewares/update_context.py` - ветка `isinstance` для
   `chat_id`/`user`/`user_id`, иначе тихо ломаются ключи FSM, диалоги и
   фильтры.
5. `docs/pages/botapi/updates.rst` (`autoclass`),
   `docs/pages/event-handling/routers.rst` (таблица событий),
   `examples/all_updates.py`.

## Новый полиморфный подтип

Union-алиас собирается из `discriminator.mapping` сам, регистрация в реторте -
ручная: без неё подтип есть в аннотациях, но не грузится, и тесты этого не
ловят. Подтип - в словарь своего семейства в `src/maxo/serialization.py`:

| Семейство          | Словарь                    | Тег на проводе  | Enum                    |
|--------------------|----------------------------|-----------------|-------------------------|
| Апдейты            | `_UPDATE_TAGS`             | `update_type`   | `UpdateType`            |
| Вложения           | `_ATTACHMENT_TAGS`         | `type`          | `AttachmentType`        |
| Вложения в запросе | `_ATTACHMENT_REQUEST_TAGS` | `type`          | `AttachmentRequestType` |
| Элементы разметки  | `_MARKUP_TAGS`             | `type`          | `MarkupElementType`     |
| Кнопки             | `_BUTTON_TAGS`             | `type`          | `ButtonType`            |

Новому вложению ещё нужны `factory()` и `to_request()` у него и у пары
`*Request`, свойство-хелпер и ветка `attachment_type` в `MessageBody`, а
заливаемому через `UploadType` - запись в `MEDIA_ATTACHMENT_FACTORIES` в
`src/maxo/bot/bot.py`. Новый метод - в `_METHOD_ROOTS` в
`src/maxo/bot/warming_up.py`.
