# FSM и dialogs

- FSM включена в `Dispatcher` по умолчанию: `MemoryStorage`,
  `SimpleEventIsolation`, `DefaultKeyBuilder`. Для нескольких процессов -
  Redis storage/isolation.
- Ключ FSM: `{bot_id}:{chat_id}:{user_id}:{destiny}`. Dialogs держат несколько
  стеков через `destiny`, поэтому им нужен
  `DefaultKeyBuilder(with_destiny=True)`; без него `destiny != "default"` даёт
  `ValueError`. `setup_dialogs` ставит такую изоляцию сам, при кастомной FSM
  проверяй совместимость ключей.
- `setup_dialogs(dp)` вызывается после подключения диалогов к роутерам.
- `Dialog` наследует `Router`, но `include()` у него кидает `TypeError`; свои
  update диалог ловит через `IntentFilter`.
- Callback payload виджета - `{intent_id}:{widget_id}:{data}`, по `intent_id`
  грузится нужный контекст. Widget `id` в окне и диалоге стабильны и уникальны.
- `manager.find(widget_id)` возвращает `ManagedWidget`, проксирующий атрибуты
  виджета и знающий `manager`; виджет расширяет его через `managed(manager)`.
- Стек - не больше 100 диалогов (`_STACK_LIMIT`).
- `new_int_id()` (время в мс + random) кодируется в короткую строку, чтобы
  уложиться в лимит длины payload. ID двух диалогов, запущенных в одну
  миллисекунду, могут совпасть - известное ограничение; формат держит короткий
  payload, обходы коллизии требуют изменения публичного контракта.

## Тесты dialogs

- Готовые хелперы: `mock_manager` в `tests/maxo_dialog/widgets/conftest.py`,
  `create_text_message`/`create_photo_message`/`setup_mock_manager` в
  `tests/maxo_dialog/widgets/input/conftest.py`, test tools из
  `maxo.dialogs.test_tools` (`BotClient`, `MockMessageManager`, memory storage,
  локаторы клавиатуры), фикстуры `tests/maxo_webhook`. Фильтры виджетов читают
  `manager.event` - передай его в `setup_mock_manager`.
- Для dialogs проверяй края: пустой текст, сообщение без body, фильтр с
  `False`, `on_error`, `page=0` и `page > max`, пустой `ListGroup`.
