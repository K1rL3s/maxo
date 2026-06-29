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

- **Быстрые ответы**: методы ``answer_text``, ``reply_text``, ``answer_photo`` и т.д. автоматически подставляют нужные ID.
- **Управление клавиатурами**: методы для быстрой отправки или редактирования клавиатур.
- **Доступ к боту**: через свойство ``facade.bot`` всегда доступен экземпляр бота.

Отправка медиа
--------------

Фасады поддерживают отправку медиа двумя способами:

- **Загрузка файла** - через ``InputFile`` (``BufferedInputFile``, ``FSInputFile``). Файл загружается на сервер автоматически.
- **По токену** - через ``MediaAttachmentsRequests`` (``PhotoAttachmentRequest``, ``VideoAttachmentRequest`` и т.д.). Используется, когда медиа уже загружено ранее и известен его токен.

Оба варианта можно передавать в параметр ``media`` методов ``send_message``, ``send_media`` и ``edit_message``. Тип ``MediaInput`` объединяет оба варианта:

.. code-block:: python

    from maxo.routing.updates.mixins.attachments import MediaInput

Загрузка файла
~~~~~~~~~~~~~~

.. code-block:: python

    from maxo.utils.upload_media import BufferedInputFile

    photo = BufferedInputFile.image(content, "photo.jpg")
    await facade.send_media(media=photo, text="Новое фото")

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

Список доступных фасадов
------------------------

Ниже приведен список всех фасадов для различных типов событий.

.. automodule:: maxo.routing.facades
   :members:
   :undoc-members:
   :show-inheritance:
