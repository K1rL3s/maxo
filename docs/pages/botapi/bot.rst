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
Запрос после ``close()`` откроет новую сессию: так одного бота можно запустить
повторно, например вторым ``run_polling``. Такую сессию тоже нужно закрыть
``bot.close()``, иначе aiohttp предупредит о незакрытой сессии.

Информация о боте
-----------------

- ``await bot.me()`` - запрашивает ``GET /me`` только при первом вызове, дальше отдаёт сохранённое.
- ``await bot.get_my_info()`` - всегда идёт в API и обновляет то, что отдаёт ``me()``.

Polling, webhook и ``async with bot`` загружают информацию сами, поэтому в хендлерах ``await bot.me()`` запроса не делает.

HTTP-клиент
-----------

Запросы к API идут через сменный HTTP-клиент unihttp ``bot.client``, по умолчанию ``default_client()``.

Токен ставит ``AuthMiddleware``, и только на относительный URL - то есть на ``base_url`` клиента API. На полный URL (вложение, ссылка на загрузку) он не уходит.

Сменить сессию, например на aiohttp с прокси:

.. code-block:: python

    from aiohttp import ClientSession, ClientTimeout, TCPConnector

    from maxo.bot.client import build_ssl_context, default_client

    session = ClientSession(
        connector=TCPConnector(ssl=build_ssl_context()),
        proxy="http://proxy:3128",
        timeout=ClientTimeout(total=60),
    )
    bot = Bot("TOKEN", client=default_client(session=session))

Сериализация, разбор ответов и базовый URL берутся из клиента. Если собираете клиент сами, передайте ``get_retort()`` в ``request_dumper`` и ``response_loader`` и ``base_url=maxo.bot.client.BASE_URL``.

Переданный снаружи клиент бот не закрывает.

Файлы
-----

Токен бота уходит только в запросы к API MAX: ``Authorization`` ставится лишь
на относительные URL методов, поэтому на хосты загрузки и скачивания он не
попадает.

- Обычная загрузка по ``upload_url`` (``bot.upload_media``) идёт через
  ``bot.client``: к ней применяются его настройки (proxy, таймауты) и middleware.
- ``Bot.download`` и resumable-загрузка (``bot.upload_media_resumable``) идут
  через отдельную ``aiohttp``-сессию, а не ``bot.client``. Настройки и middleware
  клиента к ним не применяются.

Прогрев
-------

Конструктор ``Bot`` ничего не прогревает. Загрузчики и дамперы общего ``get_retort()`` собираются лениво на первом запросе (около 2 с для всех методов). ``Dispatcher`` вызывает ``maxo.bot.warming_up.warm_up()`` при сигнале ``BeforeStartup``, поэтому polling и webhook прогреваются сами. Если ``Bot`` используется как API-клиент, вызовите ``warm_up()`` вручную.

Ошибки запросов
---------------

Все исключения - в ``maxo.errors``, общий предок - ``MaxoError``.

- ``MaxBotApiError`` - API ответил ошибкой. Подкласс выбирается по HTTP-статусу (``MaxBotBadRequestError``, ``MaxBotNotFoundError``, ``MaxBotServerError`` и т.д.), сам статус - в ``status_code``, разобранное тело - в ``code``, ``error``, ``message``, исходное - в ``raw_data``. Ответ ``200`` с ``success: false`` или ``error_code`` в теле тоже даёт ``MaxBotBadRequestError``.
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
