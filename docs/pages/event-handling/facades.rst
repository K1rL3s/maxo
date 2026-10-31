Фасады
======

Фасад - это набор методов, подмешанных прямо в объект обновления (``MessageCreated``, ``MessageCallback`` и другие), которые упрощают взаимодействие с API и работу с контекстом события. Отдельного объекта для этого не требуется - методы вызываются на самом ``update``.

Зачем нужны фасады?
-------------------

Обычно, чтобы отправить сообщение в ответ пользователю, нужно знать ``chat_id`` или ``user_id`` и вручную вызывать методы бота. В классическом подходе это выглядит так:

.. code-block:: python

    await bot.send_message(chat_id=chat_id, text="Hello!")


С использованием фасада код становится короче и понятнее, так как ``update`` уже знает контекст текущего обновления (в каком чате произошло событие, кто его инициатор):

.. code-block:: python

    @router.message_created()
    async def echo(update: MessageCreated) -> None:
        await update.answer_text("Hello!")

Основные возможности
--------------------

- **Быстрые ответы**: методы ``answer_text``, ``reply_text``, ``send_media`` и другие автоматически подставляют нужные ID.
- **Управление клавиатурами**: методы для быстрой отправки или редактирования клавиатур.
- **Доступ к боту**: через свойство ``update.bot`` всегда доступен экземпляр бота.

Отправка медиа
--------------

Фасады поддерживают отправку медиа двумя способами:

- **Загрузка файла** - через ``InputFile`` (``BufferedInputFile``, ``FSInputFile``). Файл загружается на сервер автоматически.
- **По токену** - через ``MediaAttachmentsRequests`` (``PhotoAttachmentRequest``, ``VideoAttachmentRequest`` и т.д.). Используется, когда медиа уже загружено ранее и известен его токен.

Оба варианта можно передавать в параметр ``media`` методов ``send_message``, ``send_media`` и ``edit_message``. Тип ``MediaInput`` объединяет оба варианта:

.. code-block:: python

    from maxo.types import MediaInput

Загрузка файла
~~~~~~~~~~~~~~

.. code-block:: python

    from maxo.utils.upload_media import BufferedInputFile

    photo = BufferedInputFile.image(content, "photo.jpg")
    await update.send_media(media=photo, text="Новое фото")

Фасады загружают файлы через ``bot.build_attachments``. Без апдейта, например
из фоновой задачи, вызывайте бота напрямую: ``await bot.build_attachments(...)``
или ``await bot.upload(file)``, подробнее - на странице :doc:`../botapi/bot`.

Настройки загрузки на файловый хост собраны в ``maxo.bot.UploadConfig`` и
передаются в ``Media(config=...)``, а сам ``Media`` - в ``Bot(media=...)``.
Способ выбирается полем ``method``
(``maxo.bot.UploadMethod``):

- ``AUTO`` (по умолчанию) - видео и аудио от ``resumable_threshold`` грузятся
  частями, остальное - одним запросом.
- ``RESUMABLE`` - видео и аудио всегда частями.
- ``SINGLE`` - всегда одним multipart-запросом.

Файлы и изображения всегда уходят одним запросом. Сервер файлов принимает так
и файлы больше 2 ГиБ, а загрузку частями держит только на одном соединении и
теряет после любой ошибки. Видео и аудио частями грузятся надёжнее: упавший
кусок отправляется повторно.

``FSInputFile`` при загрузке одним запросом читается с диска потоком и не
держится в памяти целиком, поэтому для больших файлов предпочитайте его.
``BufferedInputFile`` и собственные ``InputFile`` передаются целиком из памяти.

В ``UploadConfig`` также задаются размер куска и ретраи загрузки частями.
Ожидание обработки файла сервером - модель задержки и ретраи отправки при
``attachment.not.ready`` - настраивается отдельно, через
``maxo.bot.ProcessingConfig`` в ``Bot(processing=...)``. Для больших файлов
повышайте ``not_ready_max_retries`` - сервер
обрабатывает многогигабайтные файлы дольше.

.. code-block:: python

    from maxo import Bot
    from maxo.bot import Media, ProcessingConfig, UploadConfig, UploadMethod
    from maxo.utils.upload_media import FSInputFile

    # AUTO - значение по умолчанию; для очень больших файлов даём больше ретраев
    bot = Bot(
        token,
        media=Media(config=UploadConfig(method=UploadMethod.AUTO)),
        processing=ProcessingConfig(not_ready_max_retries=30),
    )

    video = FSInputFile.video("/path/to/large_video.mp4")
    await update.send_media(media=video, text="Большое видео")

Отправка по токену
~~~~~~~~~~~~~~~~~~

Если медиа уже было загружено или получено из входящего сообщения, можно использовать токен напрямую:

.. code-block:: python

    from maxo.types import PhotoAttachmentRequest

    photo = PhotoAttachmentRequest.factory(token=token)
    await update.send_media(media=photo, text="Фото по токену")

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
    await update.send_message(text="Микс медиа", media=media)

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

Ниже приведен список всех фасадов для различных типов событий. Все они
доступны из пакета: ``from maxo.types.facades import ChatMethodsFacade``.

.. automodule:: maxo.types.facades.bot
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: maxo.types.facades.chat
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: maxo.types.facades.message
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: maxo.types.facades.comment
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: maxo.types.facades.callback
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: maxo.types.facades.subscription
   :members:
   :undoc-members:
   :show-inheritance:

