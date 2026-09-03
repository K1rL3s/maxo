Фасады
======

Фасады - это обёртки, упрощающие взаимодействие с API и управление контекстом события. Они автоматически внедряются в аргументы обработчиков, если указать соответствующий тип.

Зачем нужны фасады?
-------------------

Обычно, чтобы отправить сообщение в ответ пользователю, нужно знать ``chat_id`` или ``user_id`` и вручную вызывать методы бота. В классическом подходе это выглядит так:

.. code-block:: python

    await bot.send_message(chat_id=chat_id, text="Hello!")


С использованием фасада код становится короче и понятнее, так как фасад уже знает контекст текущего обновления (в каком чате произошло событие, кто его инициатор):

.. code-block:: python

    # В аргументах хендлера: facade: MessageCreatedFacade
    await facade.answer_text("Hello!")

Основные возможности
--------------------

- **Быстрые ответы**: методы ``answer_text``, ``reply_text``, ``send_media`` и другие автоматически подставляют нужные ID.
- **Управление клавиатурами**: методы для быстрой отправки или редактирования клавиатур.
- **Доступ к боту**: через свойство ``facade.bot`` всегда доступен экземпляр бота.

Отправка медиа
--------------

Фасады поддерживают отправку медиа двумя способами:

- **Загрузка файла** - через ``InputFile`` (``BufferedInputFile``, ``FSInputFile``). Файл загружается на сервер автоматически.
- **По токену** - через ``MediaAttachmentsRequests`` (``PhotoAttachmentRequest``, ``VideoAttachmentRequest`` и т.д.). Используется, когда медиа уже загружено ранее и известен его токен.

Оба варианта можно передавать в параметр ``media`` методов ``send_message``, ``send_media`` и ``edit_message``. Тип ``MediaInput`` объединяет оба варианта:

.. code-block:: python

    from maxo.types.facades import MediaInput

Загрузка файла
~~~~~~~~~~~~~~

.. code-block:: python

    from maxo.utils.upload_media import BufferedInputFile

    photo = BufferedInputFile.image(content, "photo.jpg")
    await facade.send_media(media=photo, text="Новое фото")

Все настройки загрузки собраны в ``maxo.bot.UploadConfig`` и передаются в
``Bot(upload_config=...)``. Способ выбирается полем ``method``
(``maxo.bot.UploadMethod``):

- ``AUTO`` (по умолчанию) - большие файлы грузятся resumable-протоколом
  (частями), мелкие - одним запросом. Порог - ``resumable_threshold``.
- ``RESUMABLE`` - всегда частями.
- ``SINGLE`` - всегда одним multipart-запросом.

В ``UploadConfig`` также задаются размер куска и ретраи resumable-загрузки,
ретраи отправки при ``attachment.not.ready`` и модель ожидания обработки файла
сервером. Для больших файлов повышайте ``not_ready_max_retries`` - сервер
обрабатывает многогигабайтные файлы дольше.

Resumable-загрузка читает файл по кускам и отправляет их последовательными
запросами. Для ``FSInputFile`` это значит, что большой файл стримится прямо с
диска и не держится в памяти целиком - так снимается лимит на размер (обычный
однозапросный аплоад падает на файлах около 2 ГБ). Для больших файлов
предпочитайте ``FSInputFile``:

.. code-block:: python

    from maxo import Bot
    from maxo.bot import UploadConfig, UploadMethod
    from maxo.utils.upload_media import FSInputFile

    # AUTO - значение по умолчанию; для очень больших файлов даём больше ретраев
    config = UploadConfig(method=UploadMethod.AUTO, not_ready_max_retries=30)
    bot = Bot(token, upload_config=config)

    video = FSInputFile.video("/path/to/large_video.mp4")
    await facade.send_media(media=video, text="Большое видео")

Отправка по токену
~~~~~~~~~~~~~~~~~~

Если медиа уже было загружено или получено из входящего сообщения, можно использовать токен напрямую:

.. code-block:: python

    from maxo.types import PhotoAttachmentRequest

    photo = PhotoAttachmentRequest.factory(token=token)
    await facade.send_media(media=photo, text="Фото по токену")

Комбинирование
~~~~~~~~~~~~~~

Можно смешивать оба типа в одном вызове - порядок вложений сохраняется:

.. code-block:: python

    from maxo.types import PhotoAttachmentRequest, VideoAttachmentRequest
    from maxo.utils.upload_media import BufferedInputFile

    media = [
        BufferedInputFile.image(new_photo_bytes, "photo.jpg"),
        VideoAttachmentRequest.factory(token=existing_video_token),
    ]
    await facade.send_message(text="Микс медиа", media=media)

Комментарии к постам
--------------------

Методы ``Bot.send_comment``, ``Bot.edit_comment``, ``Bot.delete_comment``,
``Bot.get_comment_by_id`` и ``Bot.get_comments`` работают с комментариями к
постам каналов. Объект комментария имеет тип ``CommentMessage`` и поддерживает
как привычные методы ``send_message``, ``edit_message``, ``delete_message`` и
``get_message_by_id``, так и их явные алиасы с ``comment`` в названии.

.. code-block:: python

    from maxo.types import CommentCreated

    @router.comment_created()
    async def on_comment(update: CommentCreated) -> None:
        await update.reply_text("Ответ в той же ветке")

В комментариях не поддерживаются вложения, клавиатуры, ``notify=False`` и ссылки с типом ``forward``.
Фасад пишет warning и игнорирует такие параметры.
Если комментарии в канале отключены, MAX API может вернуть ``500 internal.error``.

Создание, изменение и удаление комментария приходят отдельными событиями
``comment_created``, ``comment_edited`` и ``comment_removed``. В первых двух
``update.message`` автоматически загружается как ``CommentMessage``, а методы
общего фасада вызывают API комментариев.

Список доступных фасадов
------------------------

Ниже приведен список всех фасадов для различных типов событий.

.. automodule:: maxo.routing.facades
   :members:
   :undoc-members:
   :show-inheritance:
