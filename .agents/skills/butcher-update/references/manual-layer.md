# Ручной слой поверх генерации

Перечень собран сравнением чистой генерации с закоммиченным `src/maxo`
(`just butcher --output-dir <tmp>` + `diff -ru`). Всё перечисленное butcher
**стирает** при генерации поверх `src/maxo` - и не восстанавливает.

Держи список в актуальном состоянии: если ручной кусок переехал в
`butcher/overrides.py`, вычёркивай его отсюда.

## Файлы, которые butcher не пишет вообще

Лежат в тех же каталогах и от генерации не страдают, но про них легко забыть
при чистке:

- `src/maxo/types/base.py` - `MaxoType`, `BaseMaxoType`, `MaxUpdate`,
  `BaseUpdate`, `BaseMethodsFacade`.
- `src/maxo/types/error_event.py`, `update_context.py`, `upload_media_result.py`.
- `src/maxo/bot/methods/base.py`, `markers.py`.
- Методы вне свагера: `bots/edit_bot_info.py`, `chats/delete_chat.py`,
  `chats/get_chat_by_link.py`, `chats/get_chats.py`, `chats/set_admins.py`,
  `upload/upload_media.py`.

Их реэкспорт в сгенерированные `__init__.py` держат `TYPES_EXTRA_EXPORTS` и
`METHODS_EXTRA_EXPORTS` в `butcher/overrides.py`.

## `factory()` - фабричные конструкторы

Есть у: `AudioAttachment`, `ContactAttachment`, `FileAttachment`,
`InlineKeyboardAttachment`, `PhotoAttachment`, `ShareAttachment`,
`StickerAttachment`, `VideoAttachment` и у всех парных `*Request`:
`AudioAttachmentRequest`, `ContactAttachmentRequest`, `FileAttachmentRequest`,
`InlineKeyboardAttachmentRequest`, `PhotoAttachmentRequest`,
`ShareAttachmentRequest`, `StickerAttachmentRequest`, `VideoAttachmentRequest`.

На них завязаны `maxo/routing/mixins/attachments.py`,
`maxo/utils/builders/attachment_request.py`, `maxo/utils/hide_link.py` - без
`factory` падает уже `import maxo`.

## `to_request()` - вложение в форму запроса

- `Attachment` - `@abstractmethod to_request()` плюс импорт
  `AttachmentsRequests` под `TYPE_CHECKING`.
- Реализации: `AudioAttachment`, `ContactAttachment`, `FileAttachment`,
  `InlineKeyboardAttachment`, `LocationAttachment`, `PhotoAttachment`,
  `ShareAttachment`, `StickerAttachment`, `VideoAttachment`.

## Алиасы и хелперы «подражание aiogram»

| Тип                | Ручное                                                                                   |
|--------------------|-------------------------------------------------------------------------------------------|
| `Callback`         | `id`, `data`, `unsafe_data`                                                               |
| `CallbackButton`   | `callback_data`                                                                            |
| `Chat`             | `id`                                                                                       |
| `MarkupElement`    | `offset` (алиас `from_`) - на нём держатся `utils/formatting.py`, `utils/text_decorations.py` |
| `Message`          | `message` (нужен `MessageMethodsFacade`, без него класс абстрактный)                        |
| `MessageBody`      | `id`, `keyboard`, `reply_markup`, `photo`, `video`, `audio`, `file`, `sticker`, `contact`, `share`, `location`, `_unparse_entities`, `html_text`, `md_text`, `attachment_type`, `content_type` |
| `MessageCallback`  | `callback_id`, `id`, `payload`, `data`, `user`, `from_user`                                |
| `MessageCreated`   | `text`, `user_id`                                                                          |
| `MessageEdited`    | `text`                                                                                     |
| `User`             | `id`, `fullname`, `full_name`                                                              |

## Ссылки на сообщения

`generated_url` и `unsafe_generated_url` у `Message` и `LinkedMessage` вместе с
импортом `from maxo.utils.link import id_to_message_url`.

## Поля и сужения, которых нет в спеке

- `Chat.chat_message_id: Omittable[str | None]` + `unsafe_chat_message_id`.
- `ShareAttachment.payload` - `field(default_factory=ShareAttachmentPayload)`
  вместо обязательного поля.
- `MessageCallback` - `# type: ignore[misc]` на классе, `message: Message | None`
  с `# type: ignore[assignment]`, импорты фасадов из
  `maxo.routing.mixins.callback` и `maxo.routing.mixins.message` (генератор
  печатает плоский `from maxo.routing.mixins import ...`).

`MessageButton.text` и `PhotoAttachmentRequestPayload.photos` руками уже **не**
правятся - они генерируются через `MODEL_FIELD_OVERRIDES`.

`CommentCreated.message` и `CommentEdited.message` сужаются с ошибочного
`Message` в Swagger до `CommentMessage` через `FieldOverride(ref=...)`.
`CommentMessage` наследует `Message` и `CommentMethodsFacade`, который сам
наследует `MessageMethodsFacade`: поэтому общий API сообщения сохраняется, а
`answer()` использует методы комментариев.

## Хвосты методов

- `AnswerOnCallback.notification` - поле отсутствует в актуальном Swagger,
  но поддерживается библиотекой.
- `GetUpdates` - объявление класса с `slots=False` и метод `make_response`
  (терпимость к незагружаемым апдейтам).
- `UploadMedia.validate_response` - в ручном файле, генерацией не затирается.

## Докстринги, испорченные спекой

Исходный чанк содержит незакрытые или неправильные markdown-заборы в
описаниях: `editMyCommands`, `getAdmins` (два бэктика), `sendMessage` (четыре
бэктика), `getVideoAttachmentDetails`. Также сломаны curl-примеры
`getComments`, `sendComment` и `editComment`. В `max-swagger.json` они
исправлены, чтобы генерация сразу давала корректные docstring.

## Реестры и compat-слои, о которых легко не узнать

Генерация их не трогает, но по ним расходится ручная регистрация новых
апдейтов и фасадов. Полный порядок действий - в карте касаний `SKILL.md`.

- `src/maxo/serialization.py` - `TAG_PROVIDERS`, регистрация полиморфных типов
  в retort. Union-алиасы генерируются, а эта таблица - нет.
- `src/maxo/bot/warming_up.py` - кортежи `_types` и `_methods`.
- `../../../../src/maxo/types/facades/attachments.py` - `MEDIA_ATTACHMENT_FACTORIES`,
  карта `UploadType` -> `factory` для заливаемых медиа.
- `src/maxo/routing/facades/middleware.py` - `_FACADES_MAP`, единственный путь
  от типа апдейта к `ctx["facade"]`.
- `src/maxo/routing/middlewares/update_context.py` - ветки `isinstance`,
  которые заполняют `chat_id`/`user`/`user_id` в `UpdateContext`.
- `src/maxo/routing/updates/` - депрекейтед-шим: `__init__.py` плюс
  deep-модули на каждый апдейт. **Пополняется**: новый апдейт заводится и там.
- `src/maxo/utils/facades/` - второй депрекейтед-шим (`updates/`, `methods/`,
  `middleware.py`), переехавший в `maxo.routing`. Сохраняет фасадные алиасы до
  удаления всего слоя в 0.9.0.
- `tests/maxo/routing/updates/test_deprecation.py` - ручной `parametrize` по
  модулям шима.
- `tests/maxo/routing/test_facades.py` - ручной список `CASES`.
- `tests/maxo/types/test_accessors.py` - ручные списки полей для `unsafe_*`.

## Известный дрейф: генератор впереди дерева

Обратный случай - расхождение не в пользу `src/maxo`: генератор даёт более
точный тип, а в дереве лежит старый. Это **не поломка** и не твоя ошибка.

- `Chat.participants` - в спеке `additionalProperties: integer`, генератор даёт
  `dict[str, int]`, в дереве остался `dict[str, Any]`.
- `User.name` - в спеке лежит в `required`, генератор даёт `str | None = None`,
  а в дереве `Omittable[str | None]`.

**Вердикт: в рамках обновления контракта такой дрейф не чинится.** Если файл не
попал в дельту двух генераций - не трогай его, даже если видишь расхождение.
Это отдельная задача и отдельный коммит: смена типа публичного поля ломает
пользовательский код и требует своего решения мейнтейнера. На шаге 9 такие
файлы обязаны остаться в списке расходящихся - это норма.
