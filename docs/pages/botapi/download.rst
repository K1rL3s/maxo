Скачивание вложений
===================

.. meta::
   :description: Скачивание вложений в maxo - Bot.download, Bot.download_to и
      Bot.download_stream: целиком в память, в файл на диске и чанками.
   :keywords: maxo download, скачать вложение, download_to, download_stream,
      AttachmentPayload, прогресс скачивания

.. list-table::
   :header-rows: 1
   :widths: 28 22 50

   * - Метод
     - Возвращает
     - Когда брать
   * - ``download()``
     - ``bytes``
     - файл нужен целиком в памяти
   * - ``download_to()``
     - ``None``
     - файл нужен на диске
   * - ``download_stream()``
     - контекст с чанками ``bytes``
     - всё остальное: прогресс, свой буфер, обработка на лету

Обратная операция, загрузка файлов: :doc:`../event-handling/facades`.

Что передавать
--------------

Первым аргументом идёт либо строка с URL, либо ``AttachmentPayload``:

.. code-block:: python

    from maxo import Bot
    from maxo.types import MessageCreated


    @dp.message_created()
    async def file_handler(update: MessageCreated, bot: Bot) -> None:
        file = update.message.body.file
        if file is not None:
            data = await bot.download(file.payload)

Напрямую передаются payload'ы файлов, видео, аудио и стикеров - они наследуют
``AttachmentPayload``. Изображения устроены иначе: ``PhotoAttachmentPayload``
не наследует ``AttachmentPayload``, поэтому у него берётся ``url``:

.. code-block:: python

    for photo in update.message.body.photo:
        data = await bot.download(photo.payload.url)

Ссылки на вложения живут ограниченное время. Если скачивание отложено,
запрашивайте объект заново, а не храните URL.

В память
--------

``download()`` возвращает ``bytes`` - их же принимает ``BufferedInputFile``,
поэтому скачанное сразу можно отправить обратно:

.. code-block:: python

    from maxo.utils.upload_media import BufferedInputFile


    @dp.message_created()
    async def repost_handler(update: MessageCreated, bot: Bot) -> None:
        photo = update.message.body.photo[0]
        data = await bot.download(photo.payload.url)

        copy = BufferedInputFile.image(data, "photo.jpg")
        await update.send_media(media=copy)

Метод держит файл в памяти целиком. Для видео и больших файлов берите
``download_to()`` или ``download_stream()``.

В файл
------

``download_to()`` открывает файл, пишет его чанками и закрывает сам. В памяти
за раз лежит один чанк:

.. code-block:: python

    from pathlib import Path


    @dp.message_created()
    async def save_handler(update: MessageCreated, bot: Bot) -> None:
        video = update.message.body.video[0]
        await bot.download_to(video.payload, Path("downloads") / "video.mp4")

Каталог должен существовать - метод его не создаёт.

Чанками
-------

``download_stream()`` - асинхронный контекстный менеджер, отдающий куски по
мере получения. Отдельного параметра для прогресса нет и не нужно:

.. code-block:: python

    received = 0
    async with bot.download_stream(video.payload) as chunks:
        async for chunk in chunks:
            received += len(chunk)
            await report_progress(received)

Соединение освобождается на выходе из ``async with`` - в том числе если цикл
прерван:

.. code-block:: python

    async with bot.download_stream(video.payload) as chunks:
        async for chunk in chunks:
            if is_enough(chunk):
                break

Через стрим данные пишутся в любой свой объект - буфер, архив, загрузку в S3.
Флашить и закрывать этот объект должен тот, кто его открыл:

.. code-block:: python

    import zipfile

    with zipfile.ZipFile("attachments.zip", "w") as archive:
        with archive.open("video.mp4", "w") as entry:
            async with bot.download_stream(video.payload) as chunks:
                async for chunk in chunks:
                    entry.write(chunk)

Размер чанка
------------

У всех трёх методов есть ``chunk_size`` (по умолчанию 64 KiB) - размер куска,
которым читается ответ. Увеличивать его имеет смысл на больших файлах и
быстром канале, уменьшать - когда прогресс должен обновляться чаще.

.. code-block:: python

    await bot.download_to(video.payload, "video.mp4", chunk_size=1024 * 1024)

Справочник методов - в :doc:`bot`.