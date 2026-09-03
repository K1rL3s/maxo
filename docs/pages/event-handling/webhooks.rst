
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

- **Engine**: Ядро, отвечающее за обработку входящих запросов. Оно получает запрос, проверяет его безопасность, парсит обновление и передает его в :class:`~maxo.Dispatcher`. Для одного бота есть готовый ``SingleBotEngine``, для нескольких - ``TokenEngine``; общая база - ``BaseWebhookEngine``.
- **WebAdapter**: Адаптер для конкретного веб-фреймворка (``AiohttpAdapter`` или ``FastAPIAdapter``). Он унифицирует работу с входящими запросами и позволяет **maxo** быть независимым от фреймворка.
- **Route**: Определяет, как строится URL для вебхука и как из входящего запроса извлечь параметры маршрута - например, токен бота (актуально для мульти-бот приложений).
- **Security**: Отвечает за проверку подлинности запроса, например, через проверку секретного токена в заголовке ``X-Max-Bot-Api-Secret``.

Все эти компоненты работают вместе, чтобы обеспечить надежный и гибкий прием обновлений.

.. note::

    Движки, ``Route`` и конфиги импортируются из корня пакета: ``from maxo.transport.webhook import SingleBotEngine, Route, WebhookConfig``. Адаптеры лежат каждый в своём модуле - ``maxo.transport.webhook.web.aiohttp`` и ``maxo.transport.webhook.web.fastapi`` (последний требует ``maxo[fastapi]``). ``Security`` и ``StaticSecret`` берутся из ``maxo.transport.webhook.security``.

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
            from maxo.routing.utils import collect_used_updates
            from maxo.transport.webhook import (
                Route,
                SingleBotEngine,
                WebhookConfig,
            )
            from maxo.transport.webhook.security import Security, StaticSecret
            from maxo.transport.webhook.web.aiohttp import AiohttpAdapter
            from maxo.types import MessageCreated

            dp = Dispatcher()
            bot = Bot(os.environ["TOKEN"])


            @dp.message_created()
            async def echo_handler(message: MessageCreated) -> None:
                await message.answer_text(
                    text=message.message.body.html_text,
                    format=TextFormat.HTML,
                )


            def main() -> None:
                engine = SingleBotEngine(
                    dp,
                    bot,
                    web=AiohttpAdapter(),
                    # Укажите путь, по которому к вам будут приходить апдейты из Макса
                    route=Route(base_url="https://example.com", path="/webhook"),
                    # security можно оставить None, если не используете секретный токен
                    security=Security(secret=StaticSecret("pepapig")),
                )

                app = web.Application()
                engine.register(app)

                # Подписка на вебхук: сообщаем Максу URL и нужные типы апдейтов
                async def subscribe(_app: web.Application) -> None:
                    await engine.subscribe(
                        WebhookConfig(update_types=list(collect_used_updates(dp))),
                    )

                app.on_startup.append(subscribe)
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
            from maxo.routing.utils import collect_used_updates
            from maxo.transport.webhook import (
                Route,
                SingleBotEngine,
                WebhookConfig,
            )
            from maxo.transport.webhook.security import Security, StaticSecret
            from maxo.transport.webhook.web.fastapi import FastAPIAdapter
            from maxo.types import MessageCreated

            dp = Dispatcher()
            bot = Bot(os.environ["TOKEN"])


            @dp.message_created()
            async def echo_handler(message: MessageCreated) -> None:
                await message.answer_text(
                    text=message.message.body.html_text,
                    format=TextFormat.HTML,
                )


            def main() -> FastAPI:
                engine = SingleBotEngine(
                    dp,
                    bot,
                    web=FastAPIAdapter(),
                    # Укажите путь, по которому к вам будут приходить апдейты из Макса
                    route=Route(base_url="https://example.com", path="/webhook"),
                    # security можно оставить None, если не используете секретный токен
                    security=Security(secret=StaticSecret("pepapig")),
                )

                # Сигналы startup/shutdown движок повесит сам внутри register().
                # Свой lifespan нужен только для подписки на вебхук.
                @asynccontextmanager
                async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
                    await engine.subscribe(
                        WebhookConfig(update_types=list(collect_used_updates(dp))),
                    )
                    yield

                app = FastAPI(lifespan=lifespan)
                engine.register(app)

                return app


            logging.basicConfig(level=logging.DEBUG)
            app = main()
            # TOKEN=f9LHod fastapi dev ./examples/webhook_fastapi.py

Обработка в фоне
----------------

Движок обрабатывает каждое обновление в фоновой задаче и немедленно возвращает серверу Max.ru ответ ``200 OK``. Это позволяет избежать таймаутов, если обработка обновления занимает много времени. Поведение не отключается.

Фоновые задачи не теряются при остановке: их отслеживает ``TaskTracker``, и на shutdown движок ждёт их завершения не дольше ``shutdown_timeout`` (по умолчанию 10 секунд). Пока идёт остановка, новые запросы отклоняются.

Безопасность
------------

Для проверки того, что запросы на ваш вебхук приходят именно от серверов Max.ru, используется секретный токен.

1.  Вы генерируете случайную строку (токен).
2.  Указываете её при подписке на вебхук - движок сам добавит секрет в параметры ``engine.subscribe()``, если передан ``security``.
3.  При каждом запросе сервер Max.ru будет добавлять заголовок ``X-Max-Bot-Api-Secret`` с этим токеном.
4.  **maxo** автоматически проверяет совпадение токена.

В **maxo** за это отвечает компонент ``Security``. Реализация ``StaticSecret`` позволяет задать один и тот же токен для всех ботов.

.. code-block:: python

    from maxo.transport.webhook.security import Security, StaticSecret

    security = Security(secret=StaticSecret("your-super-secret-token"))

Секрет обязан подходить под ``^[a-zA-Z0-9_-]{5,256}$`` - иначе ``StaticSecret`` бросит ``ValueError`` сразу при создании. Ограничение идёт от `самого API <https://dev.max.ru/docs-api/methods/POST/subscriptions>`_.

Кроме секрета в ``Security`` можно передать произвольные проверки - позиционными аргументами. Проверка это любой объект с методом ``verify(request, route_params) -> bool`` (протокол ``SecurityCheck``); вернула ``False`` - запрос отклонён.

Если не передать ``security`` в движок, проверка токена производиться не будет - движок предупредит об этом в логах при ``register()``.

Запуск и остановка
------------------

При использовании вебхуков жизненный цикл приложения (startup и shutdown) управляется веб-фреймворком. ``engine.register(app)`` подписывает хуки движка на события фреймворка сам - и для ``aiohttp``, и для ``FastAPI`` (адаптер вешает собственный ``lifespan`` на свой роутер).

- **startup**: вызывает сигналы ``BeforeStartup`` и ``AfterStartup`` диспетчера, подтягивает информацию о боте и кладёт в ``workflow_data`` ключи ``dispatcher``, ``app``, ``bot`` и ``webhook_engine`` - их можно принимать в хендлерах.
- **shutdown**: вызывает ``BeforeShutdown`` и ``AfterShutdown``, дожидается фоновых задач и корректно закрывает сессию бота.

Подписка на вебхук (``engine.subscribe()``) - отдельный шаг, и её вы вызываете сами: в ``app.on_startup`` у ``aiohttp`` или в своём ``lifespan`` у ``FastAPI``. Так подписку легко отключить, если URL уже зарегистрирован в Максе.