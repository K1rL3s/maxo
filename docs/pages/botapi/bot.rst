Bot
===

Создание
--------

.. code-block:: python

    from maxo import Bot

    bot = Bot("TOKEN")

    # Загрузить информацию о боте и закрыть сессию на выходе
    async with Bot("TOKEN") as bot:
        print((await bot.me()).username)

HTTP-сессия создаётся лениво при первом запросе и закрывается в ``bot.close()``.

Информация о боте
-----------------

- ``await bot.me()`` - запрашивает ``GET /me`` только при первом вызове, дальше отдаёт сохранённое.
- ``await bot.get_my_info()`` - всегда идёт в API и обновляет то, что отдаёт ``me()``.

Polling, webhook и ``async with bot`` загружают информацию сами, поэтому в хендлерах ``await bot.me()`` запроса не делает.

HTTP-клиенты
------------

Запросы идут через два клиента, у каждого свой сменный HTTP-клиент unihttp (как сессия в aiogram или ``request`` в python-telegram-bot):

.. list-table::
   :header-rows: 1

   * - Клиент
     - Куда ходит
     - HTTP-клиент
     - Токен
   * - ``bot``
     - API MAX (``platform-api2.max.ru``)
     - ``bot.client``, по умолчанию ``default_client()``
     - да
   * - ``bot.media``
     - файловые хосты: загрузка по ссылке из ``POST /uploads`` и ссылки вложений
     - ``bot.media.client``, по умолчанию ``default_media_client()``
     - нет

``bot.media`` (``maxo.bot.Media``) устроен как ``Bot``: свой HTTP-клиент, своя цепочка ``middleware`` и свои ``call_method``/``call_method_stream``. У ``Bot`` ``call_method_stream`` нет: стримить из API нечего. ``Bot`` ходит только в API и не решает, куда отправить запрос. Middleware из ``Bot(middlewares=...)`` действуют только для API, у ``bot.media.middleware`` по умолчанию только ``NetworkErrorMiddleware``.

Токен ставит ``AuthMiddleware``, и только на относительный URL - то есть на ``base_url`` клиента API. На полный URL (вложение, ссылка на загрузку) он не уходит, даже если такой запрос по ошибке отправить через ``bot``.

У клиента ``bot.media`` по умолчанию нет общего таймаута: загрузка файла в несколько гигабайт идёт минутами, а у aiohttp общий таймаут по умолчанию - 5 минут.

Сменить сессию, например на aiohttp с прокси:

.. code-block:: python

    from aiohttp import ClientSession, ClientTimeout, TCPConnector

    from maxo.bot import Media
    from maxo.bot.client import build_ssl_context, default_client, default_media_client

    def session(timeout: ClientTimeout) -> ClientSession:
        return ClientSession(
            connector=TCPConnector(ssl=build_ssl_context()),
            proxy="http://proxy:3128",
            timeout=timeout,
        )

    bot = Bot(
        "TOKEN",
        client=default_client(session=session(ClientTimeout(total=60))),
        media=Media(
            default_media_client(
                session=session(ClientTimeout(total=None, sock_read=300)),
            ),
        ),
    )

``Media(client)`` - клиент файловых хостов, ``Bot(media=...)`` подключает его к боту. У своей сессии действует её таймаут, поэтому для неё задайте его без общего лимита. Одну сессию на оба клиента передать можно, но тогда и загрузки получат её общий таймаут.

Сериализация, разбор ответов и базовый URL берутся из клиента. Если собираете клиент сами, передайте ``get_retort()`` в ``request_dumper`` и ``response_loader`` и ``base_url=maxo.bot.client.BASE_URL``.

Переданные снаружи клиенты бот не закрывает. ``bot.close()`` закрывает и ``bot.media``, но тот тоже закрывает только свой клиент по умолчанию.

Файлы: ``bot.media``
--------------------

``bot.media`` (``maxo.bot.Media``) - клиент файловых хостов: загрузка по готовой ссылке и скачивание. В API он не ходит и про ``Bot`` не знает. Полный цикл загрузки (ссылка через ``POST /uploads`` → файл в ``bot.media`` → вложение) и сборка вложений сообщения - методы ``Bot``: ``bot.upload`` и ``bot.build_attachments``.

Файлы и изображения грузятся одним запросом (файл с диска - потоком), видео и аудио от ``UploadConfig.resumable_threshold`` - частями с повтором упавшего куска.

Каждый кусок уходит с заголовком ``X-Uploading-Mode: parallel``. В документации MAX его нет, но без него сервер привязывает сессию загрузки к TCP-соединению: кусок по другому соединению из общего пула получает ``416 Range Not Satisfiable``. С заголовком куски можно слать по любым соединениям и повторять упавший по новому.

Загрузка и вложения без апдейта:

.. code-block:: python

    from maxo.enums import UploadType
    from maxo.utils.upload_media import FSInputFile

    attachments = await bot.build_attachments(
        base=[],
        keyboard=[[button]],
        files=[FSInputFile.file("report.pdf")],
    )
    await bot.send_message(chat_id=chat_id, attachments=attachments)

    video = await bot.upload(FSInputFile.video("clip.mp4"))

    # Только файловый хост: ссылка уже есть, вернёт UploadMediaResult или None
    endpoint = await bot.get_upload_url(type=UploadType.FILE)
    result = await bot.media.upload(endpoint.url, FSInputFile.file("report.pdf"))

Скачивание:

.. code-block:: python

    # file: FileAttachment из входящего сообщения
    data = await bot.media.download(file.payload)            # целиком в память
    await bot.media.download_to(file.payload, "file.bin")    # в файл

    async with bot.media.download_stream(file.payload) as chunks:  # чанками
        async for chunk in chunks:
            ...

Принимают URL или ``AttachmentPayload`` (payload файлов, видео и аудио). У фото payload другой - передайте его ``url``. Токен бота на URL вложения не отправляется.

Неочевидные моменты:

- ``build_attachments`` после загрузки ждёт ``ProcessingConfig.estimated_delay``, а ``upload`` - нет. Если отправляете вложение из ``upload`` сразу, сервер может ответить ``attachment.not.ready``; это ретраит ``AttachmentNotReadyRetryMiddleware`` в ``send_message``.
- ``files`` в ``build_attachments`` грузятся параллельно, но в результате идут в исходном порядке; готовые вложения из ``files`` не загружаются повторно.
- ``UploadMethod.RESUMABLE`` действует только на видео и аудио. Файл и изображение всегда уходят одним запросом.
- Middleware из ``Bot(middlewares=...)`` и ``bot.middleware`` на запросы к файловым хостам не действуют. Для них есть отдельный список ``bot.media.middleware`` (по умолчанию только ``NetworkErrorMiddleware``).
- В ``download_stream`` сетевые ошибки переводятся в ``MaxBotNetworkError`` только при чтении чанков; исключения из тела ``async with`` пробрасываются как есть.

.. autoclass:: maxo.bot.Media
   :members:

Прогрев
-------

``Bot(warming_up=True)`` (по умолчанию) вызывает ``maxo.bot.warming_up.warm_up()``: заранее собирает загрузчики и дамперы общего ``get_retort()``, чтобы первый запрос не тратил на это время. В тестах удобно отключать: ``Bot(..., warming_up=False)``.

Ошибки запросов
---------------

Все исключения - в ``maxo.errors``, общий предок - ``MaxoError``.

- ``MaxBotApiError`` - API ответил ошибкой. Подкласс выбирается по HTTP-статусу (``MaxBotBadRequestError``, ``MaxBotNotFoundError``, ``MaxBotServerError`` и т.д.), сам статус - в ``status_code``, разобранное тело - в ``code``, ``error``, ``message``, исходное - в ``raw_data``. Ответ ``200`` с ``success: false`` или ``error_code`` в теле тоже даёт ``MaxBotBadRequestError``.
- ``MaxBotResponseError`` - в ответе нет данных, без которых maxo не продолжит (например, токена загруженного файла).
- ``adaptix.load_error.LoadError`` - ответ не разобрался в модель maxo. Пробрасывается как есть, вместе с путём до поля.
- ``MaxBotNetworkError`` (и ``MaxBotTimeoutError``) - запрос не дошёл, повтор может помочь. ``MaxBotRequestError`` - запрос не собрать или не отправить (кривой URL и т.п.), повтор не поможет.

.. code-block:: python

    from maxo.errors import MaxBotForbiddenError, MaxBotNetworkError

    try:
        await bot.send_message(chat_id=chat_id, text="Привет")
    except MaxBotForbiddenError:
        ...  # бота удалили из чата
    except MaxBotNetworkError:
        ...  # повторить позже

API
---

.. autoclass:: maxo.Bot
   :members:
   :undoc-members:
   :show-inheritance:
