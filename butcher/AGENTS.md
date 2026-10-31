# AGENTS.md - butcher, кодогенерация maxo

Дополняет корневой `AGENTS.md`. Butcher генерирует `src/maxo/types`,
`src/maxo/enums` и `src/maxo/bot/methods` из `max-swagger.json` и
`max-swagger.yaml` в корне. Здесь - правка самого генератора; обновление
контракта MAX API - по скиллу `.agents/skills/butcher-update/SKILL.md`.

## Запуск

```bash
just butcher --output-dir .butcher/gen   # только в сторону
just butcher-test                        # тесты butcher, вне автосбора pytest
```

`--spec` - основная спека (путь или URL), `--extra-spec` - вторая публикация
(по умолчанию `max-swagger.yaml`), `--extra-spec ""` отключает слияние.
`.butcher/` в `.gitignore`.

Прямой вывод в `src/maxo` стирает ручной слой
(`.agents/skills/butcher-update/references/manual-layer.md`). Допустим только
для полной перегенерации после изменения самого butcher: на чистом дереве, с
восстановлением каждого фрагмента ручного слоя и полным прогоном проверок.

## Устройство

Разбор свагера (`allOf`, `oneOf`/`anyOf`, `nullable`, дискриминаторы, внешние
`$ref`, коллизии имён) делает PyPI-пакет `unihttp-openapi-generator` из группы
`butcher`. За butcher - только отличия maxo от свагера.

```text
merge.merge_specs()      json + yaml
  -> spec.load()              IR генератора
  -> profile.build_profile()  maxo-трансформации IR
  -> render/*                 стиль вывода maxo
  -> emit.write()             запись + ruff конфигом проекта
```

- `merge.py`: база - json (описания, `required`, ручные правки); из yaml
  добираются только отсутствующие пути, методы, схемы, свойства, параметры,
  члены enum и флаги `nullable`/`deprecated`. Части `allOf` сопоставляются по
  порядку и только при равном их числе.
- IR строится с обязательными флагами (`spec.py`): `inheritance=True` (иначе
  `PhotoAttachment` получит копию полей `Attachment`, а база станет
  union-алиасом) и `omit_optionals=True` (необязательное поле -
  `Omittable[...] = Omitted()`; дефолты свагера игнорируются).
- Docstring'и (`render/docs.py`) - как в спеке, кроме: `<br/>` -> перенос;
  `collapse_list_blanks` убирает пустые строки перед пунктами списка;
  `reflow_lists` сдвигает список на +4 только у типов и enum'ов (у методов
  списки перемешаны с curl); поле без описания с типом из `INLINE_ALIASES`
  берёт описание алиаса; параметр с `deprecated` получает абзац
  `_Устаревший параметр_` (`spec.mark_deprecated_parameters`); `unsafe_*` идут
  по алфавиту.

## Оверрайды

Всё, чем maxo намеренно отличается от свагера, - данные в `overrides.py`
(назначение каждой таблицы - в её комментарии); логика - в `profile.py`, без
зашитых имён схем. **Файл после генерации приходится одинаково править
руками - правь таблицу, а не `src/maxo`.** Неочевидное:

- Пропуск базы в `SKIP_SCHEMAS` каскадом уносит наследников; `REPLACED_BASES`
  - без каскада.
- `ENUM_EXTRAS` - только члены, которых нет ни в одной публикации, иначе дубль.
- `MODEL_FIELD_OVERRIDES`: ссылку на другую схему меняй `ref=...` (сохраняет
  `nullable`), а не `annotation` (заменяет тип целиком).
- `DEPRECATED_METHODS`: флага `deprecated` у операций нет ни в одной публикации,
  сайт сообщает об удалении прозой. Ручной устаревший метод - `ExtraExport(...,
  deprecated=True)`.
- Плоская схема с фасадом из `CLASS_MIXINS` получает корень
  `FACADE_ROOT_BASE_CLASS` (`FacadeMaxoType`) вместо `MaxoType`.

## Разработка

- Ошибку самого генератора исправляй в upstream, а не костылём в butcher;
  подъём закреплённой версии - отдельным изменением.
- Butcher вне `mypy`, но под `ruff` с конфигом проекта.
- Трансформация профиля закрывается тестом в `tests/test_profile.py`, форма
  вывода - в `tests/test_render.py`, слияние - в `tests/test_merge.py`.
  Фикстура в `tests/conftest.py` намеренно урезана: профиль должен переживать
  спеку без части схем из таблиц оверрайдов.
