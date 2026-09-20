# Changelog

История релизов автоматически собирается из [GitHub Releases](https://github.com/K1rL3s/maxo/releases) при каждой сборке документации.


## [0.9.0](https://github.com/K1rL3s/maxo/releases/tag/v0.9.0) - 2026-09-15

### What's Changed
- Обновление по сваггеру на 26.08.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/177
- feat: add `Bot.clear_subscriptions` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/180
- Refactor routing and facades, clean up imports and middleware by @m-xim in https://github.com/K1rL3s/maxo/pull/308
- fix: выполнять хендлеры-классы с `async def __call__` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/311
- ci: проверка и публикация дистрибутива, лицензии в пакете, black в линтерах by @K1rL3s in https://github.com/K1rL3s/maxo/pull/312
- fix: validate url_to_message_id input instead of guessing by @waybill-worker in https://github.com/K1rL3s/maxo/pull/309
- refactor!: удалить maxo.utils.auth_widget by @K1rL3s in https://github.com/K1rL3s/maxo/pull/314
- fix!: сохранять access_settings стека в storage by @K1rL3s in https://github.com/K1rL3s/maxo/pull/315
- fix!: StateFilter и ExceptionTypeFilter бросают ValueError без аргументов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/316
- refactor!: удалить параметр disable_web_page_preview у Window by @K1rL3s in https://github.com/K1rL3s/maxo/pull/319
- refactor!: удалить модуль maxo.utils.long_polling by @K1rL3s in https://github.com/K1rL3s/maxo/pull/322
- refactor!: setup_jinja принимает только Dispatcher by @K1rL3s in https://github.com/K1rL3s/maxo/pull/320
- fix!: inner-мидлвари родительского роутера выполняются раньше дочерних by @K1rL3s in https://github.com/K1rL3s/maxo/pull/321
- refactor!: убрать совместимость BotDefaults(disable_link_preview=None) by @K1rL3s in https://github.com/K1rL3s/maxo/pull/325
- docs: убрать из AGENTS.md упоминание удалённого routing/updates by @K1rL3s in https://github.com/K1rL3s/maxo/pull/326
- fix: останавливать ChatMembersIterator, если в ответе нет marker by @K1rL3s in https://github.com/K1rL3s/maxo/pull/323
- fix!: запретить подключать роутер к нескольким родителям by @K1rL3s in https://github.com/K1rL3s/maxo/pull/328
- fix: разрешать строковые аннотации полей в Payload.unpack by @K1rL3s in https://github.com/K1rL3s/maxo/pull/317
- test, docs: стабилизируй test_nested_transitions, поправь пример превью и AGENTS.md by @K1rL3s in https://github.com/K1rL3s/maxo/pull/329
- refactor!: переименовал RetvalReturnedServerException в RetvalReturnedError by @K1rL3s in https://github.com/K1rL3s/maxo/pull/330
- fix!: add_share принимает url и token только по имени by @K1rL3s in https://github.com/K1rL3s/maxo/pull/331
- fix: добавил check_disabled в next, back, update, show, answer_callback by @K1rL3s in https://github.com/K1rL3s/maxo/pull/332
- chore: поднял pytest и httpx2 до версий без уязвимостей by @K1rL3s in https://github.com/K1rL3s/maxo/pull/333
- fix!: InvalidWebAppInitDataError вместо TypeError при разборе init data by @K1rL3s in https://github.com/K1rL3s/maxo/pull/327
- refactor!: feed_update больше не привязывает бота к апдейту by @K1rL3s in https://github.com/K1rL3s/maxo/pull/334
- fix: maxo-dialog-preview запускается без extra preview и понимает --help by @K1rL3s in https://github.com/K1rL3s/maxo/pull/324
- build!: исправил границы зависимостей и lowest-direct в CI by @K1rL3s in https://github.com/K1rL3s/maxo/pull/337
- fix!: decode_payload отклоняет невалидный base64 своей ошибкой by @K1rL3s in https://github.com/K1rL3s/maxo/pull/335
- fix: пропустил события фонового менеджера для недоступного стека by @K1rL3s in https://github.com/K1rL3s/maxo/pull/336
- fix: научил Calendar переключать год с 29 февраля by @K1rL3s in https://github.com/K1rL3s/maxo/pull/338
- fix: add_location принимает координаты float и Decimal by @K1rL3s in https://github.com/K1rL3s/maxo/pull/339
- fix!: feed_update без бота перестал падать с KeyError by @K1rL3s in https://github.com/K1rL3s/maxo/pull/343
- fix: добавил quote, heading и highlighted в разметку render() by @K1rL3s in https://github.com/K1rL3s/maxo/pull/342
- fix!: научил bg() работать из поста в канале без пользователя by @K1rL3s in https://github.com/K1rL3s/maxo/pull/345
- fix!: bg() сохранил текущий стек для того же чата и пользователя by @K1rL3s in https://github.com/K1rL3s/maxo/pull/346
- fix: SignalObserver пропускает хендлер по SkipHandler by @K1rL3s in https://github.com/K1rL3s/maxo/pull/341
- fix: обходил общий observer под несколькими ключами один раз by @K1rL3s in https://github.com/K1rL3s/maxo/pull/344
- fix: перестал отправлять пустой types в get_updates без обработчиков by @K1rL3s in https://github.com/K1rL3s/maxo/pull/340
- fix: BgManager.fg() перестал зависать без хендлера fg и при отмене by @K1rL3s in https://github.com/K1rL3s/maxo/pull/348
- fix!: расширил протокол DialogManager методами ManagerImpl by @K1rL3s in https://github.com/K1rL3s/maxo/pull/318


### Нейро release notes

Главное в релизе: удалены фасады-обёртки и устаревшие шимы, битый ввод в `decode_payload` и init data мини-приложений теперь даёт собственные исключения, у роутинга поменялись порядок inner-мидлварей и правило подключения роутеров, `feed_update` больше не привязывает бота к апдейту, а `bg()` в диалогах работает из постов в канале и не теряет текущий стек

#### Критические изменения

- **Удалены фасады-обёртки и аргумент `facade` в хендлерах.** Пакеты `maxo.routing.facades` (все `*Facade` и `BaseUpdateFacade`), `FacadeMiddleware` и `FACADE_KEY` удалены, ключа `ctx["facade"]` больше нет. Методы вызываются на самом апдейте:

  ```python
  # было
  async def handler(update: MessageCreated, facade: MessageCreatedFacade) -> None:
      await facade.answer_text("Привет")

  # стало
  async def handler(update: MessageCreated) -> None:
      await update.answer_text("Привет")
  ```

  Вместе с ними ушли пути импорта `maxo.routing.mixins`, `maxo.routing.updates` и `maxo.utils.facades`, теперь это `ImportError`. Миксины переехали в модули `maxo.types.facades.*`, импортируйте из конкретного файла, например `from maxo.types.facades.attachments import MediaInput`. Апдейты импортируйте из `maxo.types`. `maxo.types.BotMixin` переименован в `BaseMethodsFacade` и доступен только как `from maxo.types.facades.base import BaseMethodsFacade`. У `ErrorEvent` больше нет методов подписок (`get_subscriptions`, `subscribe` и т.д.), вызывайте их через `event.bot`
  Closes #120, #272
  by @m-xim in https://github.com/K1rL3s/maxo/pull/308
- **Удалён модуль `maxo.utils.long_polling`.** Импортируйте `LongPolling` из `maxo.transport.long_polling` или запускайте поллинг через `Dispatcher.run_polling` / `Dispatcher.start_polling`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/322
- **У `Window` удалён параметр `disable_web_page_preview`.** Передача параметра теперь падает с `TypeError`. Вместо него добавьте в окно виджет `LinkPreview(is_disabled=True)` из `maxo.dialogs.widgets.link_preview`:

  ```python
  Window(Const("Текст"), LinkPreview(is_disabled=True), state=MySG.first)
  ```

  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/319
- **`setup_jinja` принимает только `Dispatcher`.** Форма `setup_jinja(bot)` удалена, пишите `setup_jinja(dp)`. Виджет `Jinja` больше не ищет окружение на объекте бота: если его нет в `middleware_data`, используется окружение по умолчанию
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/320
- **`BotDefaults(disable_link_preview=None)` больше не поддерживается.** Поле стало `Omittable[bool]`. Чтобы не задавать значение по умолчанию, просто не передавайте аргумент. Переданный `None` не проходит mypy, а в рантайме уходит в запрос как `disable_link_preview=false`
  Closes #239
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/325
- **Удалён `maxo.utils.auth_widget`.** Модуль проверял подпись по протоколу Telegram Login Widget, которого в MAX нет, и на настоящих данных всегда возвращал `False`. Данные мини-приложений проверяйте через `maxo.utils.webapp.check_webapp_signature` и `safe_parse_webapp_init_data`
  Closes #183
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/314
- **`RetvalReturnedServerException` переименован в `RetvalReturnedError`.** Алиаса со старым именем нет, обновите импорты из `maxo.errors` / `maxo.exceptions`
  Closes #282
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/330
- **`parse_webapp_init_data` бросает `InvalidWebAppInitDataError` вместо `TypeError` и `json.JSONDecodeError`.** Неизвестные поля в init data, `user` и `chat` теперь игнорируются, JSON разбирается только в `user` и `chat`: значения в скобках в других полях, например `start_param`, остаются строками. Исключение наследует `ValueError`, так что `except ValueError` вокруг `safe_parse_webapp_init_data` продолжает работать
  Closes #242
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/327
- **`decode_payload` отклоняет невалидный base64 через `InvalidPayloadError`.** Раньше мусорные символы молча выкидывались, и `DeeplinkFilter(deep_link_encoded=True)` пропускал payload `"!!!"` как пустую строку. Вместо `binascii.Error` и `UnicodeDecodeError` теперь приходит `InvalidPayloadError` (наследует `ValueError`), а строки с лишним паддингом вроде `"aGk=="` больше не декодируются. Ошибки своего `decoder` пробрасываются как есть
  Closes #299
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/335
- **`StateFilter()` и `ExceptionTypeFilter()` без аргументов бросают `ValueError` при создании.** Раньше такой фильтр никогда не срабатывал, и хендлер молча пропадал
  Closes #288
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/316
- **`AttachmentRequestBuilder.add_share` принимает `url` и `token` только по имени.** `add_share("https://...")` теперь падает с `TypeError`, пишите `add_share(url="https://...")`
  Closes #307
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/331
- **Inner-мидлвари родительского роутера выполняются раньше дочерних**, как в aiogram. Порядок для `dp -> child`:

  ```text
  было:  child_inner_pre, dp_inner_pre, handler, dp_inner_post, child_inner_post
  стало: dp_inner_pre, child_inner_pre, handler, child_inner_post, dp_inner_post
  ```

  Если дочерняя inner-мидлварь готовила данные для родительской, перенесите эту логику
  Closes #203
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/321
- **Роутер можно подключить только к одному родителю.** Повторный `include` того же роутера, в том числе в другой `Dispatcher`, бросает `RouterAlreadyIncludedError` из `maxo.errors`. У роутера появилось свойство `parent_router`, сторонним реализациям протокола `BaseRouter` нужно добавить его вместе с сеттером
  Closes #232
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/328
- **`Dispatcher.feed_update` больше не привязывает бота к апдейту.** Long polling, webhook и `BotClient` из test tools уже отдают привязанные апдейты. Если вы собираете апдейт руками, привяжите бота сами, иначе методы на апдейте упадут с `AttributeIsEmptyError`:

  ```python
  await dp.feed_update(update.as_(bot), bot)
  ```

  `.as_` привязывает только сам объект, вложенные `Message` и `Callback` остаются без бота
  Closes #294
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/334
- **`feed_update` без бота перестал падать с `KeyError: 'bot'`.** Ошибка хендлера теперь доходит до `dp.errors` или наружу как есть. Без бота `FSMContext` не создаётся, а `Command` не совпадает с командой, где указано упоминание (`/start@name`), если не включён `ignore_mention`. `Command.parse_command` и `validate_mention` принимают `bot: Bot | None`, подклассам с переопределением нужно расширить сигнатуру для mypy. Диалоги без бота по-прежнему не работают
  Closes #202
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/343
- **`access_settings` стека диалогов сохраняются в storage.** Раньше после перечитывания стек, открытый с `AccessSettings(user_ids=[1])`, становился доступен любому участнику чата. Стеки, сохранённые прошлой версией, грузятся без миграции со значением по умолчанию
  Closes #196
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/315
- **Протокол `DialogManager` расширен членами `disabled`, `check_disabled()`, `dialog()`, `storage()` и `is_event_simulated()`.** `manager.dialog()` теперь работает и в колбэках внутри `ListGroup`. Сторонним реализациям `DialogManager` нужно добавить эти пять членов, иначе создание экземпляра упадёт с `TypeError`
  Closes #197
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/318
- **`bg()` работает из поста в канале без пользователя.** `DialogUpdateEvent.user` и параметр `user` у `BgManager` стали `User | None`, `BgManagerFactory.bg` принимает `user_id: int | None`. Рантайм существующих вызовов не меняется, но код, читающий `event.user.id`, нужно проверить на `None`, а свою реализацию `BgManagerFactory` привести к новой сигнатуре
  Closes #216
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/345
- **`bg()` без `user_id` и `chat_id` продолжает текущий стек.** Раньше он всегда уходил в стек по умолчанию, и `bg().update()` из диалога, открытого с `StartMode.NEW_STACK`, не перерисовывал окно. Если нужен прежний сброс, передайте `stack_id=DEFAULT_STACK_ID` (из `maxo.dialogs`)
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/346
- **Подняты нижние границы extras: `magic_filter>=1.0.10`, `dishka>=1.3.0`.** Более старые версии и так не работали с maxo. Заодно `fastapi>=0.128.0,<1.0.0` на всех версиях Python, разрешены `cachetools` 7 и `redis` 8
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/337

#### Новое

- **`Bot.clear_subscriptions`** удаляет WebHook-подписки параллельно, кроме переданных в `active_urls` (строка или набор строк), и возвращает `ClearSubscriptionsResult` со списками `removed` и `kept`. Ошибки удаления собираются в `ExceptionGroup` из `UnsubscribeError`. `start_polling`, `run_polling` и `LongPolling` получили флаг `clear_subscriptions=True`, а без него поллинг предупреждает в логе об активных подписках
  Closes #178
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/180
- **`disable_link_preview` в ответе на колбэк** по сваггеру на 26.08.2026: параметр есть у `AnswerOnCallback` и `callback_answer`, значение из `BotDefaults` применяется и к нему
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/177

#### Исправления

- Хендлеры-классы с `async def __call__` снова выполняются, в том числе в `on_click` / `on_success` диалогов: раньше тело не запускалось, а апдейт считался обработанным. Хендлеры под `functools.wraps`-декоратором больше не падают с `TypeError` на лишних ключах из `ctx`
  Closes #182
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/311
- `bool` в квери уходит как `true` / `false`. `User.last_activity_time` стал `Omittable[datetime]`, потому что API его не всегда присылает, для гарантированного доступа есть `unsafe_last_activity_time`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/177
- `Payload.unpack` понимает строковые аннотации и `from __future__ import annotations`: `flag=False` больше не распаковывается в `"0"`
  Closes #195
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/317
- `ChatMembersIterator` больше не зацикливается, если в ответе нет `marker`
  Closes #207
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/323
- `maxo-dialog-preview` запускается без extra `preview` и понимает `--help`, неверные аргументы дают понятную ошибку
  Closes #186
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/324
- Фоновый менеджер: события для стека, закрытого для пользователя, пропускаются без `TypeError`, а `async with bg.fg()` поднимает `StackAccessDeniedError`. `fg()` больше не зависает, если событие не дошло до хендлера (например, `UnknownIntent` после закрытия диалога) или вызывающий код отменён
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/336, https://github.com/K1rL3s/maxo/pull/348
- `next`, `back`, `update`, `show` и `answer_callback` на закрытом менеджере бросают `IncorrectBackgroundError`
  Closes #260
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/332
- `BgFactoryMiddleware` выполняется один раз на dialog-событие, а не четыре
  Closes #231
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/344
- `Calendar` переключает год с 29 февраля без `ValueError`
  Closes #214
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/338
- `SkipHandler` в хендлерах `before_startup` / `after_startup` / `before_shutdown` / `after_shutdown` пропускает хендлер, а не роняет запуск
  Closes #292
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/341
- Long polling без обработчиков не отправляет пустой `types=` и пишет предупреждение
  Closes #226
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/340
- `Text.render()` возвращает `QuoteMarkup`, `HeadingMarkup` и `HighlightedMarkup` вместо базового `MarkupElement`
  Closes #243
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/342
- `add_location` принимает `float` без ошибки mypy
  Closes #306
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/339
- `url_to_message_id` игнорирует query и fragment, а на некорректной ссылке бросает `ValueError` вместо случайного числа
  Closes #302
  by @waybill-worker in https://github.com/K1rL3s/maxo/pull/309


### New Contributors
* @waybill-worker made their first contribution in https://github.com/K1rL3s/maxo/pull/309


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.8.3...v0.9.0


## [0.8.3](https://github.com/K1rL3s/maxo/releases/tag/v0.8.3) - 2026-08-26

### What's Changed
- Добавил `MaxBotBadGatewayError` для 502 ошибки by @K1rL3s in https://github.com/K1rL3s/maxo/pull/175
- Исправил дамп даты-время в таймстамп в квери by @K1rL3s in https://github.com/K1rL3s/maxo/pull/176


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.8.2...v0.8.3


## [0.8.2](https://github.com/K1rL3s/maxo/releases/tag/v0.8.2) - 2026-08-25

### What's Changed
- Поддержка комментариев по сваггеру на 25 Aug 2026 10:29:32 GMT by @K1rL3s in https://github.com/K1rL3s/maxo/pull/174


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.8.1...v0.8.2


## [0.8.1](https://github.com/K1rL3s/maxo/releases/tag/v0.8.1) - 2026-08-17

### What's Changed

- Чуть перфоманса by @K1rL3s in https://github.com/K1rL3s/maxo/pull/158
  - Ускорил импорт диалогов и поправил прогрев реторты
  - Сделал реторту в `maxo.dialogs.context.storage` "приватной" и убрал с неё прогрев
- Сваггер на 22.07.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/161
- feat(dialogs): двойной рендер медиа при edit на iOS by @K1rL3s in https://github.com/K1rL3s/maxo/pull/157
  - Добавлен флаг `Window.two_step_media_edit` (по умолчанию выключен).\
  Когда он включён, редактирование "медиа -> медиа" при ShowMode.EDIT выполняется в два шага
- ! fix(routing): AttributeIsEmptyError вместо AttributeError в MessageCallback без message by @biradrags in https://github.com/K1rL3s/maxo/pull/163
- chore(deps): bump extractions/setup-just from 3 to 4 by @dependabot[bot] in https://github.com/K1rL3s/maxo/pull/169
- chore(deps): bump actions/setup-python from 6 to 7 by @dependabot[bot] in https://github.com/K1rL3s/maxo/pull/170
- chore(deps): bump codecov/codecov-action from 6 to 7 by @dependabot[bot] in https://github.com/K1rL3s/maxo/pull/171
- chore(deps): bump actions/checkout from 6 to 7 by @dependabot[bot] in https://github.com/K1rL3s/maxo/pull/172
- `flags` для хендлеров by @K1rL3s in https://github.com/K1rL3s/maxo/pull/168
- Кодогенерация by @K1rL3s in https://github.com/K1rL3s/maxo/pull/165
- ! Фикс передачи `None` (`null`) в квери параметры by @K1rL3s in https://github.com/K1rL3s/maxo/pull/173

#### Breaking changes?

- `MessageCallbackFacade.message` теперь имеет тип `Message | None` и возвращает `None`, когда исходное сообщение удалено. Раньше свойство было `Message` и выбрасывало `AttributeIsEmptyError`. Это может сломать строгую типизацию и код, рассчитывающий на прежнее исключение
- Удален `DialogAttachmentsFacade`, но это внутренний модуль, не экспортируемый публичным API: `src/maxo/dialogs/manager/attachment_facade.py`
- `DeleteAdmin` сохранен как алиас `DeleteAdmins`; обычные импорты и вызовы совместимы.

**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.8.0...v0.8.1


## [0.8.0](https://github.com/K1rL3s/maxo/releases/tag/v0.8.0) - 2026-07-12

### What's Changed
* Typing/mypy fix errors by @begezyan in https://github.com/K1rL3s/maxo/pull/127
* Сваггер на 17.06.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/129
* feat: hide_link - превью-ссылка через ShareAttachment by @biradrags in https://github.com/K1rL3s/maxo/pull/132
* Алиас `MediaAttachment.file_id` к `media_id` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/135
* Запуск тестов на минимальных и максимальных версиях зависимостей by @K1rL3s in https://github.com/K1rL3s/maxo/pull/134
* Исправил `BgManager._load` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/138
* `platform-api2` и сертификат Минцифры by @K1rL3s in https://github.com/K1rL3s/maxo/pull/137
* `ConfirmButton` - кнопка с двойным подтверждением by @K1rL3s in https://github.com/K1rL3s/maxo/pull/130
* Добавил `OpenAppButton` в `KeyboardBuilder` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/139
* feat: SyncFilter - синхронная функция как фильтр by @biradrags in https://github.com/K1rL3s/maxo/pull/131
* Фикс пустого `MessageCreated.message` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/140
* Генерация слопа by @K1rL3s in https://github.com/K1rL3s/maxo/pull/142
* add payload in dialogs WebApp by @cwerti in https://github.com/K1rL3s/maxo/pull/141
* Поддержка `*filters` при регистрации обработчика by @K1rL3s in https://github.com/K1rL3s/maxo/pull/143
* Щедрый фикс всех линтеров от курсорыча, куклода и кукодекса by @tsk8r in https://github.com/K1rL3s/maxo/pull/145
* Умная нейрослоп задержка загрузки файлов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/144
* Сваггер на 10.07.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/148
* feat: CallbackAnswerMiddleware - авто-ответ на колбэк by @biradrags in https://github.com/K1rL3s/maxo/pull/133
* Перенос апдейтов в типы by @K1rL3s in https://github.com/K1rL3s/maxo/pull/149
* Чистка перед релизом by @K1rL3s in https://github.com/K1rL3s/maxo/pull/155

### New Contributors
* @cwerti made their first contribution in https://github.com/K1rL3s/maxo/pull/141

### Нейро release notes

Главное в релизе: переход на `platform-api2.max.ru` с сертификатом Минцифры, умная загрузка медиа вместо фиксированной паузы, переезд апдейтов в `maxo.types` и несколько портов удобных вещей из `aiogram`

#### Критические изменения

- **Апдейты переехали из `maxo.routing.updates` в `maxo.types`.** Старые импорты продолжают работать, но кидают `DeprecationWarning`. Обновите импорты на `from maxo.types import MessageCreated, MessageCallback, ...`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/149
- **Фильтры при регистрации обработчика стали строго позиционными** (`*filters`). Вызов `@router.message_created(filter=MyFilter())` больше не работает - пишите `@router.message_created(MyFilter())`. Зато теперь можно передать несколько фильтров сразу, они склеиваются по `И`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/143
- **Базовый URL сменился на `https://platform-api2.max.ru/`**, а `MaxApiClient` теперь ходит в апи с сертификатом Минцифры (сертификат вшит в пакет)
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/137
- **Удалён нерабочий `maxo.types.chat_button.ChatButton`**
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/148
- **`GET /chats` доживает последние дни.** С июня 2026 апи перестаёт отдавать список чатов бота; собирайте `chat_id` из событий `bot_added` / `bot_started` и храните у себя. Подробности - в docstring `GetChats`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/148

#### Новое

- **Умная загрузка файлов.** Вместо фиксированной паузы `0.5` секунды после загрузки вложений появился `UploadConfig` с режимами `AUTO`, `SINGLE` и `RESUMABLE`. Большие файлы льются чанками и не читаются в память целиком, задержка перед отправкой оценивается по типу и размеру файла, а ошибка `attachment.not.ready` ретраится с backoff через `AttachmentNotReadyRetryMiddleware`. Настраивается через `Bot(upload_config=...)`.
  Closes #10
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/144
- **`CallbackAnswerMiddleware`** - автоматический ответ на колбэк до или после хендлера. Механизма flags в maxo нет, поэтому конфигурация идёт через мутабельный `CallbackAnswer` в `ctx`: объявите параметр `callback_answer: CallbackAnswer` в хендлере и меняйте поведение на лету.
  Closes #67
  by @biradrags in https://github.com/K1rL3s/maxo/pull/133
- **`SyncFilter`** - синхронная функция или лямбда в качестве фильтра, с флагами `run_in_thread` (для блокирующих предикатов) и `exceptions_as_false`.
  Closes #66
  by @biradrags in https://github.com/K1rL3s/maxo/pull/131
- **`hide_link`** - Max-аналог одноимённого хелпера из aiogram. В отличие от aiogram возвращает не строку для вставки в текст, а `ShareAttachmentRequest`, который кладётся в `attachments`.
  Closes #65
  by @biradrags in https://github.com/K1rL3s/maxo/pull/132
- **`ConfirmButton`** - кнопка с двойным подтверждением для диалогов, без отдельного окна под подтверждение. Состояние не хранится в dialog data, поэтому между переключениями окон кнопка сбрасывается в исходный вид
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/130
- **`KeyboardBuilder.add_open_app`** - шорткат для `OpenAppButton`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/139
- **`payload` у WebApp в диалогах**
  by @cwerti in https://github.com/K1rL3s/maxo/pull/141
- **`MessageCallback.answer` как `callback_answer`**, а также алиасы для привычек из aiogram: `Callback.data` рядом с `payload`, `MediaAttachment.file_id` как алиас к `media_id`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/135
- **Типизированные сетевые ошибки**: `MaxBotNetworkError` и `MaxBotTimeoutError` - транспортные ошибки `aiohttp` и `unihttp` больше не протекают наружу как есть

#### Исправления

- Фикс загрузки `MessageCreated` с пустым `message` - ломалось на голосовых сообщениях
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/140
- Фикс `BgManager._load`: для диалогов нельзя использовать `bot.get_members`, да и вызывался он неправильно
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/138
- `ChatsIterator` и `ChatMembersIterator` больше не зацикливаются: `marker=None` означает последнюю страницу, а не запрос первой
- `KeyboardBuilder.add()` больше не содержит мёртвой закомментированной валидации
- `maxo.utils.callback_answer` не тянет за собой deprecated-шим и не кидает чужой `DeprecationWarning`
- Исправлено описание `disable_link_preview`: превью отключается при `true`, а не при `false`

#### Внутреннее, CI и типизация

- Обновление типов, методов, енумов и апдейтов по сваггеру на 17.06.2026 и 10.07.2026. `SetAdmins` стал алиасом к `PostAdmins`
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/129, https://github.com/K1rL3s/maxo/pull/148
- Починены все ошибки `mypy` в `src/maxo`, `tests` и `examples`, плюс конфиги `codespell` / `slotscheck` / `bandit`
  by @tsk8r in https://github.com/K1rL3s/maxo/pull/145
- Аннотации типов в тестах
  by @begezyan in https://github.com/K1rL3s/maxo/pull/127
- Тесты гоняются на минимальных и максимальных версиях зависимостей
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/134
- Скиллы для ИИ-агентов
  by @K1rL3s in https://github.com/K1rL3s/maxo/pull/142


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.7.0...v0.8.0


## [0.7.0](https://github.com/K1rL3s/maxo/releases/tag/v0.7.0) - 2026-06-03

### What's Changed
- fix: justfile duplicate recipe error on windows by @begezyan in https://github.com/K1rL3s/maxo/pull/126
- Сваггер 01.06.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/128
- `MessageCallback.answer` как `callback_answer` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/125
  - ! `CallbackMethodsFacade.answer = callback_answer`. Конфликт с `MessageMethodsFacade.answer` в `MessageCallback`
  - `CallbackMethodsFacade.callback_answer`: `text` как `notification`
  - `Message` отнаследован от `MessageMethodsFacade`


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.6.0...v0.7.0


## [0.6.0](https://github.com/K1rL3s/maxo/releases/tag/v0.6.0) - 2026-05-09

### What's Changed

- Мега пример диалогов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/102
  - Перекопировал мега пример из оригинальных диалогов
  - Добавил пару алиасов для подражания аиограму и диалогам
- Убрал из `MagicData` и `MagicFilter` лишний `.cast(bool)` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/105
- Улучшение вывода ошибок by @K1rL3s in https://github.com/K1rL3s/maxo/pull/106
  - **!** Добавил `AddMembers` в исключения для патча `success=false` и `status=200`
  - Убрал дублирование информации в выводе ошибок
- Улучшение документации by @goduni in https://github.com/K1rL3s/maxo/pull/109
- Пропертя `user_id` для `MessageCreated` by @Bakhtovar03 in https://github.com/K1rL3s/maxo/pull/100
- Сваггер 28.04.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/116
  - Добавил `ContactAttachmentPayload.hash`, починил ссылки на доку в типах
- `CopyText` и улучшения диалогов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/118
- `BotMixin` и прокидывание бота через реторту by @K1rL3s in https://github.com/K1rL3s/maxo/pull/103
  - **!** Перенёс фасады из `maxo.utils.facades` в `maxo.routing.facades`
  - **!** Удалил `maxo.utils.helpers` и `request_to_attachment` оттуда
  - Добавил `class BotMixin`, `MaxoType(BaseMaxoType, BotMixin)`, сделал передачу бота в датаклассы через реторту
  - Отнаследовал `Bot` от `unihttp.clients.base.BaseAsyncClient`, чтобы убрать ошибки `mypy` на `bind_method`
  - Разделил `create_retort` на `create_retort` и `create_retort_with_bot`
  - Дополнительно отнаследовал `AttributeIsEmptyError` от `AttributeError`
  - Убрал `@final`, так как его надо поставить много где, но проще тупо убрать
  - Отнаследовал фасады от `SubscriptionMethodsFacade` , где они наследовались от `BotMethodsFacade`
  - Исправил ошибки `slotscheck` и настроил `.justfile`
  - Переделал доку под `update.<method>` вместо фасадов
  - Добавил `maxo/loggers.py`: `dialogs = logging.getLogger("maxo.dialogs")`
- Поправлены ошибки тайпхинтов связанные с фасадами by @tsk8r in https://github.com/K1rL3s/maxo/pull/107
- perf(dialogs): параллельные show + answer_callback в _callback_handler by @biradrags in https://github.com/K1rL3s/maxo/pull/114
- fix(dialogs): storage_proxy и access_validator корректно обрабатывают channel-сообщения без user by @biradrags in https://github.com/K1rL3s/maxo/pull/112
- feat(dialogs)!: убрать лишний get_message_by_id после edit и remove_kbd by @biradrags in https://github.com/K1rL3s/maxo/pull/113
- Сваггер на 04.05.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/124
- Продолжение подражания `aiogram`'у by @K1rL3s in https://github.com/K1rL3s/maxo/pull/123
  - **!** `Dispatcher.feed_update`: `ctx["bots"]` со списком из одного бота, и добавление `ctx["bot"]` только при переданном боте
  - **!** `Window.parse_mode` по умолчанию `Omitted`, а не `None`, чтобы работали дефолты бота
  - `ParseMode = TextFormat`
  - `AttachmentType.PHOTO = IMAGE`
  - `BaseObserver.outer_middleware` как `BaseObserver.middleware.outer`, `MiddlewareManagerFacade.__call__` как `BaseObserver.middleware.inner`
  - `maxo.exceptions` как алиас к `maxo.errors`
  - Передача аргументов в мидлвари позиционно, чтобы можно было писать любые имена аргументов
  - `MessageCallback.id = callback_id`
  - `Observer.register = handler`
  - `Router.edited_message = message_edited`
  - `User.full_name = fullname`

### New Contributors
* @tsk8r made their first contribution in https://github.com/K1rL3s/maxo/pull/107
* @Bakhtovar03 made their first contribution in https://github.com/K1rL3s/maxo/pull/100

**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.5.3...v0.6.0


## [0.5.3](https://github.com/K1rL3s/maxo/releases/tag/v0.5.3) - 2026-04-11

### What's Changed

- Фикс кодгена и моделей by @K1rL3s in https://github.com/K1rL3s/maxo/pull/94
- Фикс работы `ListGroup` не с `CallbackButton` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/95
- Обновил версии зависимостей by @K1rL3s in https://github.com/K1rL3s/maxo/pull/96
- Диалоги 2.6.0 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/97
- Кнопка `Clipboard` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/98
- Сваггер `platform-api.max.ru` на 08.04.2026 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/101


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.5.2...v0.5.3


## [0.5.2](https://github.com/K1rL3s/maxo/releases/tag/v0.5.2) - 2026-04-03

### What's Changed
* Исправление порядка обхода роутеров при срабатывании фильтра by @begezyan in https://github.com/K1rL3s/maxo/pull/90
* Установил `format: Omittable[TextFormat | None] = Omitted()` в фасадах by @K1rL3s in https://github.com/K1rL3s/maxo/pull/93
* Фикс автоинжекта дишки by @K1rL3s in https://github.com/K1rL3s/maxo/pull/92


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.5.1...v0.5.2


## [0.5.1](https://github.com/K1rL3s/maxo/releases/tag/v0.5.1) - 2026-03-31

### What's Changed

Исправлены ишаки #75 #78 #79 #84

- fix: pass chat_type to BgManager instead of hardcoding ChatType.CHAT by @biradrags in https://github.com/K1rL3s/maxo/pull/81
- docs: добавить страницу форматирования текста by @biradrags in https://github.com/K1rL3s/maxo/pull/82
- Фикс установки дефолтов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/83
- Исправление наследования inner middleware by @begezyan in https://github.com/K1rL3s/maxo/pull/85
- Фикс диалоговских`CallableObject`, фикс сохранения аттачментов в стэке by @K1rL3s in https://github.com/K1rL3s/maxo/pull/86
- Поддержка `Highlighted` и `Heading` разметки текста, фикс `LoadError` в `LongPolling` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/87
- feat: test_tools документация, render_transitions, примеры, исправление preview.py by @biradrags in https://github.com/K1rL3s/maxo/pull/80
- Поддержка отправки `MediaAttachmentsRequests` через фасады by @K1rL3s in https://github.com/K1rL3s/maxo/pull/88
  - docs: раздел отправки медиа в документации фасадов by @biradrags in https://github.com/K1rL3s/maxo/pull/89


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.5.0...v0.5.1


## [0.5.0](https://github.com/K1rL3s/maxo/releases/tag/v0.5.0) - 2026-03-19

### What's Changed

Исправлены ишаки #7 #16 #24 #25 #61 #68

- feat: улучшение информации о репозитории и гайд для контрибьюторов by @goduni in https://github.com/K1rL3s/maxo/pull/63

- feat: добавлена страница документации про `Omitted`-`Omittable` by @goduni in https://github.com/K1rL3s/maxo/pull/70

- feat: добавлена страница документации про сигналы жизненного цикла by @goduni in https://github.com/K1rL3s/maxo/pull/71

- docs: исправлены неточности в документации webhooks и useful_notes by @goduni in https://github.com/K1rL3s/maxo/pull/73

- aiogram-like by @K1rL3s in https://github.com/K1rL3s/maxo/pull/61
  - Форматирование текста через `maxo.utils.formatting.Text` и пример этого
  - Скачивание файлов по ссылкам через бота и макс-апи-клиент
  - `AttachmentType.DOCUMENT = AttachmentType.FILE`, `ContentType = AttachmentType`
  - `maxo.types.message_callback.CallbackQuery = MessageCallback`
  - Опциональное использование `FSM` флагом в `Dispatcher`
  - Проперти для медиа-аттачментов в `MessageBody`
  - Алиас `maxo.filters` к `maxo.routing.filters`
  - Ключ `"state"` c `FsmContext`
  - Методы `BaseRouter.include_router` и `BaseRouter.include_routers`
  - `Router.message = Router.message_created`, `Router.callback_query = Router.message_callback` для подражания аиограму
  - Дока про вебхуки
  - Дока полезные заметки 
  - Пример одной `FSM` для ТГ и Макса
  - Пример приёма аттачмента от юзера и отправка их копий обратно
  - Пример мидлварей для ботов
  - Обновление моделей по кодгену
  - Вынос реторты в `maxo/serlalization.py`
  - Учёт миллисекунд в `new_int_id` для генерации интент-айди в диалогах
  - Починил поддержку `AttachmentsRequests | Attachments`
  - Убрал `Button` из `InlineButtons`, багалась реторта
  - Вебхуки на основе [aiogram-webhook](https://github.com/m-xim/aiogram-webhook) для аиохттп и фастапи

- Транспортный модуль для получения апдейтов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/77

### Breaking changes:
- `BotDefault` для дефолтов бота, переделан `Bot.__init__`

  Было:
  ```python
  class Bot:
      def __init__(
          self,
          token: str,
          text_format: TextFormat | None = None,
          warming_up: bool = True,
      ) -> None:
  ```
  Стало:
  ```python
  class Bot:
      def __init__(
          self,
          token: str,
          *,
          defaults: BotDefaults | None = None,
          warming_up: bool = True,
          middleware: list[AsyncMiddleware] | None = None,
          json_dumps: Callable[[Any], str] = json.dumps,
          json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
      ) -> None:
  ```

- Перенос `ComandObject` из `maxo.types.command_object` в `maxo.routing.filters.command`

  Было:
  ```python
  from maxo.types import CommandObject
  from maxo.types.command_object import CommandObject
  ```
  Стало:
  ```python
  from maxo.routing.filters import CommandObject
  from maxo.routing.filters.command import CommandObject
  ```
  
- Перенос `LongPolling` из `maxo.utils.long_polling` в `maxo.transport.long_polling`

  Было:
  ```python
  from maxo.utils.long_polling import LongPolling
  ```
  Стало:
  ```python
  from maxo.transport.long_polling import LongPolling
  ```

- `MaxoUpdate` стал наследником `BaseUpdate` вместо `BaseSignal`, его обсервер в `Dispatcher` стал `UpdateObserver` вместо `SignalObserver`

  Было:
  ```python
  from maxo.routing.signals.base import BaseSignal
  
  class MaxoUpdate(BaseSignal, Generic[_UpdateT]):
      ...
  ```
  ```python
  from maxo.routing.observers import SignalObserver
  
  class Dispatcher(Router):
      update: SignalObserver[MaxoUpdate[Any]]
  ```
  
  Стало:
  ```python
  from maxo.routing.updates.base import BaseUpdate
  
  class MaxoUpdate(BaseUpdate, Generic[_UpdateT]):
      ...
  ```
  ```python
  from maxo.routing.observers import UpdateObserver
  
  class Dispatcher(Router):
      update: UpdateObserver[MaxoUpdate[Any]]
  ```


- Переименовал `maxo.utils.link.create_telegram_link` -> `create_http_max_link`
- Переименовал `maxo.utils.link.create_tg_link` -> `create_telegram_link`

**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.4.1...v0.5.0


## [0.4.1](https://github.com/K1rL3s/maxo/releases/tag/v0.4.1) - 2026-02-25

### What's Changed
* Новые объекты по обновлению `dev.max.ru` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/60


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.4.0...v0.4.1


## [0.4.0](https://github.com/K1rL3s/maxo/releases/tag/v0.4.0) - 2026-02-25

### What's Changed

- Уведомления в тг-чат через `reagento/relator` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/43
  - Воркфлоу депендабота

- Фикс `with_destiny=True` при использовании `setup_dialogs` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/49
  - Фикс ишака #34
  - Вынос `magic_filter` в опциональные зависимости #41

- Медийные личности, `BgManager` и зелёные тесты by @K1rL3s in https://github.com/K1rL3s/maxo/pull/50
  - Восстановление `MediaId`, `MediaIdStorage`, `CachedMediaId`, `MediaIdStorageProtocol`
  - Восстановление `Window.render_link_preview`
  - Поддержка медиагрупп (нескольких `Media` виджетов в одном `Window`)
  - Сделал виджет `MultiMedia(Media)`, аналог `Multi(Text)`
  - Поддержка в диалогах `BotAddedToChat`, `BotRemovedFromChat`, `BotStopped`, `UserAddedToChat`, `UserRemovedFromChat`
  - Починил "переотправку" сообщения с диалогом, если от юзера пришло сообщение не по теме
  - Заменил `ChatType.CHAT` на `ChatType.DIALOG` там, где неправильно изменил их в коммите `64044213`
  - Рабочий `BgManager`, фикс работы в группах
  - Вынес ключи `"fsm_storage"`, `"fsm_context"`, `"raw_state"`, `"facade"` в переменные, починил `MessageManager.had_media` и `MessageManager.need_media`
  
- Фикс типизации `UpdateHandlerFn` и `SignalHandlerFn` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/53

- Добавление аннотаций типов by @begezyan in https://github.com/K1rL3s/maxo/pull/55
  - Устранение жалоб mypy c 754 до 604 errors. Указал аннотации типов в тестах.

- Test, Lint, Formating by @m-xim in https://github.com/K1rL3s/maxo/pull/54
  - Разделение analyze на lint и test. Корректировка ruff, mypy

- Добавил метод `Attachment.to_request` для перевода аттачмента в запрос by @K1rL3s in https://github.com/K1rL3s/maxo/pull/58
  - Поддержка `Attachments` в типах там, где есть `AttachmentsRequests` за счёт адаптикса
  - Убрал `type` перед юнион-тайпами, потому что адаптикс не хавает их

- UpdateContext mw by @biradrags in https://github.com/K1rL3s/maxo/pull/52
  - Расширен тип `UpdateContext` полями `chat: Chat | None` и `user: User | None`; при обогащении заполняется также `type` из `chat.type`.
  - В `_resolve_update_context` добавлены все типы апдейтов
  - В `_resolve_user` добавлены все апдейты с пользователем в payload.
  - Обогащение включается параметром конструктора `UpdateContextMiddleware(enrich=True)` или ключом в `workflow_data` - `enrich_update_context=True` (например, `LongPolling.run(bot, enrich_update_context=True)`). По умолчанию выключено, чтобы не нагружать Bot API.
  - Добавлен логгер `maxo.routing.update_context`; при обогащении - `debug`, при ошибках API - `warning` с `exc_info`.

- dishka examples by @biradrags in https://github.com/K1rL3s/maxo/pull/51

- Документация для библиотеки by @goduni in https://github.com/K1rL3s/maxo/pull/56
  - Создана документация для библиотеки на основе `sphinx` & `shibuya`.

### Breaking changes (#50, #58)
- Переделал `NewMessage` с `attachments` на `media` + `keyboard`
- Удалил лишние поля из `LinkPreviewOptions`
- `AttachmentsFacade.build_attachments` аргумент `media` переименовал в `files`
- `AttachmentsFacade.build_media_attachments` аргумент `media` переименовал в `files`
- `AttachmentsFacade.upload_media` аргумент `media` переименовал в `file`
- `MediaWidget.render_media` возвращаемый тип был `MediaAttachment | None`, стал `list[MediaAttachment]`
- Удалил методы `MessageManager`: `get_media_source`, `need_reply_keyboard`, `had_voice`, `need_voice`
- Удалил `maxo/utils/helpers/attachments.py` - `def attachment_to_request`

### New Contributors
- @biradrags made their first contribution in https://github.com/K1rL3s/maxo/pull/52

**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.3.0...v0.4.0


## [0.3.0](https://github.com/K1rL3s/maxo/releases/tag/v0.3.0) - 2026-02-17

### What's Changed
* CI workflow, тесты, покрытие by @begezyan in https://github.com/K1rL3s/maxo/pull/33
* Фасады, `TextDecoration` (поддержка html/md), breaking changes by @K1rL3s in https://github.com/K1rL3s/maxo/pull/30
* Fix badges in readme by @m-xim in https://github.com/K1rL3s/maxo/pull/37
* update to unihttp 0.2.5 by @goduni in https://github.com/K1rL3s/maxo/pull/38
* `unsafe_*` методы для типов и апдейтов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/39
* Поддержка 3.14 by @K1rL3s in https://github.com/K1rL3s/maxo/pull/40

### Breaking changes (#30)
* Удалил `maxo/enums/text_fromat.py` из-за опечатки в названии файла
* Перенёс `StateFilter` из `maxo/fsm/filter.py` в `maxo/routing/filters/state.py`
* Переименовал `maxo/fsm/manager.py` в `maxo/fsm/context.py`
* Удалил из `maxo/types` неподдерживаемые `HeadingMarkup`, `HighlightedMarkup`, `NewMessage`
* Перенёс `maxo/utils/long_polling/long_polling.py` в `maxo/utils/long_polling.py`
* Удалил `Message.unsafe_body`, так как `body` есть всегда
* Удалил `maxo.enums.intent.Intent`

### New Contributors
* @begezyan made their first contribution in https://github.com/K1rL3s/maxo/pull/33
* @m-xim made their first contribution in https://github.com/K1rL3s/maxo/pull/37
* @goduni made their first contribution in https://github.com/K1rL3s/maxo/pull/38

**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.2.1...v0.3.0


## [0.2.1](https://github.com/K1rL3s/maxo/releases/tag/v0.2.1) - 2026-02-12

### What's Changed
* Исправил кодген под реалии документации и починил загрузку файлов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/29
  * [Фикс кодгена под логику документации](https://github.com/K1rL3s/maxo/pull/29/commits/f444846a6c30a5a9dbb50d6694621c6020dbe374)
  * [Фикс загрузки файлов](https://github.com/K1rL3s/maxo/pull/29/commits/cf2c4661b20f033868a4ba4c7f6de1e62d4ffccb)
  * [Документация по полям моделей](https://github.com/K1rL3s/maxo/pull/29/commits/e1a02b27f0637599676e1901444252fa1ca54a87)
  * [Убрал неподдерживаемые модели](https://github.com/K1rL3s/maxo/pull/29/commits/f98f981f0a6edcfed5232ee2f8631347868697d3)


**Full Changelog**: https://github.com/K1rL3s/maxo/compare/v0.2.0...v0.2.1


## [0.2.0](https://github.com/K1rL3s/maxo/releases/tag/v0.2.0) - 2026-02-04

### Что изменилось
* Refactor upload logic to support all attachment types by @hakkiai in https://github.com/K1rL3s/maxo/pull/19
* Фикс outer-мидлварей by @K1rL3s in https://github.com/K1rL3s/maxo/pull/21
* Перенос `Payload` с датакласса на `MaxoType` by @K1rL3s in https://github.com/K1rL3s/maxo/pull/23
* fix(TypeError: functools.partial(<function inject_router at 0x74595c2… by @TheLovii in https://github.com/K1rL3s/maxo/pull/27
* fix(calendar_kbd): убрал пустой текст и payload в календаре by @TheLovii in https://github.com/K1rL3s/maxo/pull/28
* Кодген типов и методов by @K1rL3s in https://github.com/K1rL3s/maxo/pull/26

### Новые контрибуторы
* @hakkiai made their first contribution in https://github.com/K1rL3s/maxo/pull/19
* @K1rL3s made their first contribution in https://github.com/K1rL3s/maxo/pull/21
* @TheLovii made their first contribution in https://github.com/K1rL3s/maxo/pull/27

**Полный чейнджлог**: https://github.com/K1rL3s/maxo/commits/v0.2.0

### Ссылки

[PyPI](https://pypi.org/project/maxo/0.2.0/)

### Критические изменения (#26)

Был переезд с [retejo](https:..github.com.IvanKirpichnikov.retejo) на [unihttp](https:..github.com.goduni.unihttp):
- `__http_method__` переименован в `__method__`
- Переименованы маркеры аргументов (`UrlVar` -> `Path`, `QueryParam` -> `Query`)
- `retejo.http.entities.FileObj` заменён на `unihttp.http.UploadFile`
- Взяты `Omitted`.`Omittable` из `adaptix`.
- В `maxo.omit` костылится `Omitted.__bool__ = lambda _: False`, это абсолютно осознанное решение, живите с этим

Изменения в полях:
- `maxo.bot.methods.chats.get_chat_by_link.GetChatByLink`:
  - `url` -> `chat_link`
- `maxo.bot.methods.base.MaxoMethod`:
  - `access_token` -> удалён
- `maxo.enums.markup_element_type.MarkupElementType`
  - `HEADING` -> удалён
  - `HIGHLIGHTED` -> удалён

Все модели из `maxo.bot.method_results` были перенесены в `maxo.types`, самого `maxo.bot.method_results` больше нет.

Эти типы были заменены на единый `maxo.types.simple_query_result.SimpleQueryResult`:
- `maxo.bot.method_results.chats.add_chat_administrators.AddChatAdministratorsResult`
- `maxo.bot.method_results.chats.add_chat_members.AddChatMembersResult`
- `maxo.bot.method_results.chats.delete_chat.py.DeleteChatResult`
- `maxo.bot.method_results.chats.delete_chat_member.DeleteChatMemberResult`
- `maxo.bot.method_results.chats.delete_me_from_chat.DeleteMeFromChatResult`
- `maxo.bot.method_results.chats.delete_pin_message.DeletePinMessageResult`
- `maxo.bot.method_results.chats.pin_message.PinMessageResult`
- `maxo.bot.method_results.chats.revoke_administrator_rights.RevokeAdministratorRightsResult`
- `maxo.bot.method_results.chats.send_chat_action.SendChatActionResult`
- `maxo.bot.method_results.messages.callback_answer.CallbackAnswerResult`
- `maxo.bot.method_results.messages.delete_message.DeleteMessageResult`
- `maxo.bot.method_results.messages.edit_message.EditMessageResult`

Переименнованные/перемещённые объекты:
- `maxo.bot.method_results.chats.get_chat_administrators.GetChatAdministratorsResult` -> `maxo.types.chat_members_list.ChatMembersList`
- `maxo.bot.method_results.chats.get_chat_members.GetChatMembersResult` -> `maxo.types.chat_members_list.ChatMembersList`
- `maxo.bot.method_results.chats.get_chats.GetChatsResult` -> `maxo.types.chat_list.ChatList`
- `maxo.bot.method_results.chats.get_pin_message.GetPinMessageResult` -> `maxo.types.get_pinned_message_result.GetPinnedMessageResult`
- `maxo.bot.method_results.messages.get_messages.GetMessagesResult` -> `maxo.types.message_list.MessageList`
- `maxo.bot.method_results.subscriptions.get_updates.GetUpdatesResult` -> `maxo.types.update_list.UpdateList`
- `maxo.bot.method_results.upload.get_download_link.GetDownloadLinkResult` -> `maxo.types.uploaded_info.UploadedInfo`
- `maxo.bot.method_results.upload.upload_media.UploadImagePhotoTokenResult` -> `maxo.types.photo_token.PhotoToken`
- `maxo.bot.method_results.upload.upload_media.UploadMediaResult` -> `maxo.types.upload_endpoint.UploadEndpoint`
- `maxo.bot.methods.bots.get_bot_info.GetBotInfo` -> `maxo.bot.methods.bots.get_my_info.GetMyInfo`
- `maxo.bot.methods.chats.add_chat_administrators.AddChatAdministrators` -> `maxo.bot.methods.chats.set_admins.SetAdmins`
- `maxo.bot.methods.chats.add_chat_members.AddChatMembers` -> `maxo.bot.methods.chats.add_members.AddMembers`
- `maxo.bot.methods.chats.delete_chat_member.DeleteChatMember` -> `maxo.bot.methods.chats.remove_member.RemoveMember`
- `maxo.bot.methods.chats.delete_me_from_chat.DeleteMeFromChat` -> `maxo.bot.methods.chats.leave_chat.LeaveChat`
- `maxo.bot.methods.chats.delete_pin_message.DeletePinMessage` -> `maxo.bot.methods.chats.unpin_message.UnpinMessage`
- `maxo.bot.methods.chats.get_chat_administrators.GetChatAdministrators` -> `maxo.bot.methods.chats.get_admins.GetAdmins`
- `maxo.bot.methods.chats.get_chat_members.GetChatMembers` -> `maxo.bot.methods.chats.get_members.GetMembers`
- `maxo.bot.methods.chats.get_me_chat_membership.GetMeChatMembership` -> `maxo.bot.methods.chats.get_membership.GetMembership`
- `maxo.bot.methods.chats.get_pin_message.GetPinMessage` -> `maxo.bot.methods.chats.get_pinned_message.GetPinnedMessage`
- `maxo.bot.methods.chats.revoke_administrator_rights.RevokeAdministratorRights` -> `maxo.bot.methods.chats.delete_admin.DeleteAdmin`
- `maxo.bot.methods.chats.send_chat_action.SendChatAction` -> `maxo.bot.methods.chats.send_action.SendAction`
- `maxo.bot.methods.messages.callback_answer.CallbackAnswer` -> `maxo.bot.methods.messages.answer_on_callback.AnswerOnCallback`
- `maxo.bot.methods.messages.get_message.GetMessage` -> `maxo.bot.methods.messages.get_message_by_id.GetMessageById`
- `maxo.bot.methods.messages.get_video_info.GetVideoInfo` -> `maxo.bot.methods.messages.get_video_attachment_details.GetVideoAttachmentDetails`
- `maxo.bot.methods.upload.get_download_link.GetDownloadLink` -> `maxo.bot.methods.upload.get_upload_url.GetUploadUrl`
- `maxo.enums.chat_action_type.ChatActionType` -> `maxo.enums.sender_action.SenderAction`
- `maxo.enums.chat_status.ChatStatusType` -> `maxo.enums.chat_status.ChatStatus`
- `maxo.enums.intent.IntentType` -> `maxo.enums.intent.Intent`
- `maxo.enums.keyboard_button_type.KeyboardButtonType` -> `maxo.enums.button_type.ButtonType`
- `maxo.enums.text_fromat.TextFormat` -> `maxo.enums.text_format.TextFormat`
- `maxo.routing.signals.update.Update` -> `maxo.routing.signals.update.MaxoUpdate`
- `maxo.routing.updates.bot_added.BotAdded` -> `maxo.routing.updates.bot_added_to_chat.BotAddedToChat`
- `maxo.routing.updates.bot_removed.BotRemoved` -> `maxo.routing.updates.bot_removed_from_chat.BotRemovedFromChat`
- `maxo.routing.updates.chat_title_changed.ChatTitileChanged` -> `maxo.routing.updates.chat_title_changed.ChatTitleChanged`
- `maxo.routing.updates.user_added.UserAdded` -> `maxo.routing.updates.user_added_to_chat.UserAddedToChat`
- `maxo.routing.updates.user_removed.UserRemoved` -> `maxo.routing.updates.user_removed_from_chat.UserRemovedFromChat`
- `maxo.types.callback_keyboard_button.CallbackKeyboardButton` -> `maxo.types.callback_button.CallbackButton`
- `maxo.types.chat_membership.ChatMembership` -> `maxo.types.chat_member.ChatMember`
- `maxo.types.image_attachment.ImageAttachment` -> `maxo.types.photo_attachment.PhotoAttachment`
- `maxo.types.image_attachment_request.ImageAttachmentRequest` -> `maxo.types.photo_attachment_request.PhotoAttachmentRequest`
- `maxo.types.keyboard_buttons.KeyboardButtons` -> `maxo.types.buttons.InlineButtons`
- `maxo.types.link_keyboard_button.LinkKeyboardButton` -> `maxo.types.link_button.LinkButton`
- `maxo.types.message_keyboard_button.MessageKeyboardButton` -> `maxo.types.message_button.MessageButton`
- `maxo.types.open_app_keyboard_button.OpenAppKeyboardButton` -> `maxo.types.open_app_button.OpenAppButton`
- `maxo.types.request_attachments.AttachmentsRequests` -> `maxo.types.attachments.AttachmentsRequests`
- `maxo.types.request_attachments.MediaAttachmentsRequests` -> `maxo.types.attachments.MediaAttachmentsRequests`
- `maxo.types.request_contact_keyboard_button.RequestContactKeyboardButton` -> `maxo.types.request_contact_button.RequestContactButton`
- `maxo.types.request_geo_location_button.RequestGeoLocationKeyboardButton` -> `maxo.types.request_geo_location_button.RequestGeoLocationButton`
- `maxo.types.video_info.VideoInfo` -> `maxo.types.video_attachment_details.VideoAttachmentDetails`

Новые объекты:
- `maxo.bot.methods.subscriptions.get_subscriptions.GetSubscriptions`
- `maxo.bot.methods.subscriptions.subscribe.Subscribe`
- `maxo.bot.methods.subscriptions.unsubscribe.Unsubscribe`
- `maxo.enums.reply_button_type.ReplyButtonType`
- `maxo.errors.api.MaxBotUnknownServerError`
- `maxo.routing.updates.bot_stopped.BotStopped`
- `maxo.routing.updates.dialog_cleared.DialogCleared`
- `maxo.routing.updates.dialog_muted.DialogMuted`
- `maxo.routing.updates.dialog_removed.DialogRemoved`
- `maxo.routing.updates.dialog_unmuted.DialogUnmuted`
- `maxo.types.attachment.Attachment`
- `maxo.types.attachment_payload.AttachmentPayload`
- `maxo.types.attachment_request.AttachmentRequest`
- `maxo.types.button.Button`
- `maxo.types.buttons.ReplyButtons`
- `maxo.types.chat_admins_list.ChatAdminsList`
- `maxo.types.chat_button.ChatButton`
- `maxo.types.data_attachment.DataAttachment`
- `maxo.types.emphasized_markup.EmphasizedMarkup`
- `maxo.types.get_subscriptions_result.GetSubscriptionsResult`
- `maxo.types.heading_markup.HeadingMarkup`
- `maxo.types.highlighted_markup.HighlightedMarkup`
- `maxo.types.link_markup.LinkMarkup`
- `maxo.types.markup_element.MarkupElement`
- `maxo.types.monospaced_markup.MonospacedMarkup`
- `maxo.types.photo_tokens.PhotoTokens`
- `maxo.types.reply_button.ReplyButton`
- `maxo.types.reply_keyboard_attachment.ReplyKeyboardAttachment`
- `maxo.types.reply_keyboard_attachment_request.ReplyKeyboardAttachmentRequest`
- `maxo.types.send_contact_button.SendContactButton`
- `maxo.types.send_geo_location_button.SendGeoLocationButton`
- `maxo.types.send_message_button.SendMessageButton`
- `maxo.types.simple_query_result.SimpleQueryResult`
- `maxo.types.strikethrough_markup.StrikethroughMarkup`
- `maxo.types.strong_markup.StrongMarkup`
- `maxo.types.subscription.Subscription`
- `maxo.types.underline_markup.UnderlineMarkup`
- `maxo.types.user_mention_markup.UserMentionMarkup`
