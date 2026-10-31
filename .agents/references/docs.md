# Документация и примеры

- Sphinx в `docs/`, страницы в `rst`, changelog - `docs/pages/changelog.md`.
  Новые страницы - в `docs/index.rst` и нужный `toctree`. `docs/_build/` не
  коммить.
- Новая пользовательская возможность - обновить docs и, если уместно,
  `examples/`. README - короткие примеры, подробности - в `docs/pages/`.
- В примерах: явные observers (`message_created`, `message_callback`), алиасы -
  только как совместимость; клавиатуры через
  `maxo.utils.builders.KeyboardBuilder`; magic filter через
  `maxo.integrations.magic_filter.MagicFilter`; webhook через `SimpleEngine`,
  `AiohttpWebAdapter`/`FastApiWebAdapter`, `StaticRouting`, `Security`,
  `StaticSecretToken`, `collect_used_updates`.
- После правок `docs/conf.py`, `_static`, `_extra/llms.txt` или sitemap проверь
  сборку: `just docs`.
