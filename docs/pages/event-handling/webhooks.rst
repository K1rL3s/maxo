
Webhooks
========

Вебхуки (Webhooks) - это мощный способ получения обновлений от API Max.ru. Вместо того, чтобы постоянно опрашивать сервер (как в :doc:`long-polling`), вы предоставляете URL-адрес (endpoint), на который сервер будет сам отправлять новые события.

Этот метод является **предпочтительным для продакшн-среды**, так как он более эффективен и позволяет строить масштабируемые решения.

.. note::

    Для использования вебхуков ваш бот должен быть доступен по публичному IP-адресу, и на сервере должен быть настроен SSL-сертификат (Max.ru требует HTTPS).

Когда использовать Webhooks?
-----------------------------

- **Продакшн-среда**: Вебхуки идеально подходят для ботов, работающих в реальных условиях.
- **Высокая нагрузка**: Если ваш бот обрабатывает большое количество событий, вебхуки обеспечат лучшую производительность.
- **Масштабируемость**: Вы можете запускать несколько экземпляров бота за балансировщиком нагрузки (например, Nginx), который будет распределять входящие обновления между ними.

Как это работает
----------------

Система вебхуков в **maxo** построена на нескольких ключевых компонентах:

- **WebhookEngine**: Ядро, отвечающее за обработку входящих запросов. Оно получает запрос, проверяет его безопасность, парсит обновление и передает его в :class:`~maxo.Dispatcher`.
- **WebAdapter**: Адаптер для конкретного веб-фреймворка (например, `aiohttp` или `FastAPI`). Он унифицирует работу с входящими запросами и позволяет **maxo** быть независимым от фреймворка.
- **Routing**: Определяет, как строится URL для вебхука и как из входящего запроса извлечь токен бота (актуально для мульти-бот приложений).
- **Security**: Отвечает за проверку подлинности запроса, например, через проверку секретного токена в заголовке ``X-Max-Bot-Api-Secret``.

Все эти компоненты работают вместе, чтобы обеспечить надежный и гибкий прием обновлений.

Примеры использования
---------------------

**maxo** поддерживает несколько популярных веб-фреймворков "из коробки".

.. tabs::

    .. tab:: aiohttp

        .. code-block:: python

            import logging
            import os

            from aiohttp import web

            from maxo import Bot, Dispatcher
            from maxo.enums import TextFormat
            from maxo.routing.updates import MessageCreated
            from maxo.routing.utils import collect_used_updates
            from maxo.transport.webhook.adapters.aiohttp.adapter import AiohttpWebAdapter
            from maxo.transport.webhook.engines import SimpleEngine, WebhookEngine
            from maxo.transport.webhook.routing import StaticRouting
            from maxo.transport.webhook.security import Security, StaticSecretToken

            dp = Dispatcher()
            bot = Bot(os.environ["TOKEN"])


            @dp.message_created()
            async def echo_handler(message: MessageCreated) -> None:
                await message.answer_text(
                    text=message.message.body.html_text,
                    format=TextFormat.HTML,
                )


            @dp.after_startup()
            async def on_startup(dispatcher: Dispatcher, webhook_engine: WebhookEngine) -> None:
                await webhook_engine.set_webhook(update_types=collect_used_updates(dispatcher))


            def main() -> None:
                engine = SimpleEngine(
                    dp,
                    bot,
                    web_adapter=AiohttpWebAdapter(),
                    # Укажите путь, по которому к вам будут приходить апдейты из Макса
                    routing=StaticRouting(url="https://example.com/webhook"),
                    # security можно оставить None, если не используете секретный токен
                    security=Security(secret_token=StaticSecretToken("pepapig")),
                )
                app = web.Application()
                engine.register(app)
                web.run_app(app, host="127.0.0.1", port=8080)


            if __name__ == "__main__":
                logging.basicConfig(level=logging.DEBUG)
                main()

    .. tab:: FastAPI

        .. code-block:: python

            import logging
            import os
            from collections.abc import AsyncGenerator
            from contextlib import asynccontextmanager

            from fastapi import FastAPI

            from maxo import Bot, Dispatcher
            from maxo.enums import TextFormat
            from maxo.routing.updates import MessageCreated
            from maxo.routing.utils import collect_used_updates
            from maxo.transport.webhook.adapters.fastapi.adapter import FastApiWebAdapter
            from maxo.transport.webhook.engines import SimpleEngine, WebhookEngine
            from maxo.transport.webhook.routing import StaticRouting
            from maxo.transport.webhook.security import Security, StaticSecretToken

            dp = Dispatcher()
            bot = Bot(os.environ["TOKEN"])


            @dp.message_created()
            async def echo_handler(message: MessageCreated) -> None:
                await message.answer_text(
                    text=message.message.body.html_text,
                    format=TextFormat.HTML,
                )


            @dp.after_startup()
            async def on_startup(dispatcher: Dispatcher, webhook_engine: WebhookEngine) -> None:
                await webhook_engine.set_webhook(update_types=collect_used_updates(dispatcher))


            def main() -> FastAPI:
                engine = SimpleEngine(
                    dp,
                    bot,
                    web_adapter=FastApiWebAdapter(),
                    # Укажите путь, по которому к вам будут приходить апдейты из Макса
                    routing=StaticRouting(url="https://example.com/webhook"),
                    # security можно оставить None, если не используете секретный токен
                    security=Security(secret_token=StaticSecretToken("pepapig")),
                )

                # В реализации FastApiWebAdapter в register игнорируются переданные
                # on_startup и on_shutdown. Разработчик должен сам определить lifespan,
                # в котором вызовет engine.on_startup и engine.on_shutdown для корректной работы
                @asynccontextmanager
                async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
                    engine.register(app)
                    await engine.on_startup(app)
                    yield
                    await engine.on_shutdown(app)

                return FastAPI(lifespan=lifespan)


            logging.basicConfig(level=logging.DEBUG)
            app = main()
            # TOKEN=f9LHod fastapi dev ./examples/webhook_fastapi.py

Обработка в фоне
----------------

По умолчанию ``WebhookEngine`` обрабатывает каждое обновление в фоновой задаче (``asyncio.create_task``) и немедленно возвращает серверу Max.ru ответ ``200 OK``. Это позволяет избежать таймаутов, если обработка обновления занимает много времени.

Такое поведение можно отключить, передав ``handle_in_background=False`` в конструктор движка. В этом случае ответ серверу будет отправлен только после полного выполнения вашего хендлера.

Безопасность
------------

Для проверки того, что запросы на ваш вебхук приходят именно от серверов Max.ru, используется секретный токен.

1.  Вы генерируете случайную строку (токен).
2.  Указываете ее при подписке на вебхук (метод `subscribe`).
3.  При каждом запросе сервер Max.ru будет добавлять заголовок ``X-Max-Bot-Api-Secret`` с этим токеном.
4.  **maxo** автоматически проверяет совпадение токена.

В **maxo** за это отвечает компонент ``Security``. Реализация ``StaticSecretToken`` позволяет задать один и тот же токен для всех ботов.

.. code-block:: python

    from maxo.transport.webhook.security import Security, StaticSecretToken

    security = Security(secret_token=StaticSecretToken("your-super-secret-token"))

Если не передать ``security`` в движок, проверка токена производиться не будет.

Запуск и остановка
------------------

При использовании вебхуков жизненный цикл приложения (startup и shutdown) управляется веб-фреймворком. **maxo** предоставляет хуки ``on_startup`` и ``on_shutdown``, которые должны быть вызваны в соответствующие моменты.

- ``on_startup``: Вызывает ``BeforeStartup`` и ``AfterStartup`` сигналы диспетчера, а также инициализирует сессию бота. Установку вебхука рекомендуется выполнять в обработчике ``after_startup`` через ``webhook_engine.set_webhook()``.
- ``on_shutdown``: Вызывает ``BeforeShutdown`` и ``AfterShutdown``, а также корректно закрывает сессию бота.

В примере с ``aiohttp`` адаптер делает это автоматически. В ``fastapi`` это нужно сделать вручную через `lifespan` менеджер.
