Мидлвари
========

Мидлвари позволяют перехватывать и изменять события **до** или **после** их обработки обработчиками. Это инструмент для логирования, обработки ошибок, внедрения зависимостей (DI) и управления контекстом.

В **maxo** есть два типа мидлварей, которые работают на разных этапах обработки события:

1.  **Outer Middleware** (внешние): выполняются *до* того, как сработают фильтры обработчика. Они оборачивают процесс поиска обработчика. Используйте их, если нужно выполнить действие для всех обновлений данного типа (например, логирование, установка глобального контекста, обработка ошибок).
2.  **Inner Middleware** (внутренние): выполняются *после* того, как фильтры конкретного обработчика прошли успешно, но *перед* (и после) самим обработчиком. Используйте их, если действие зависит от того, будет ли вызван обработчик (например, транзакции базы данных, специфичные проверки прав).

.. mermaid::

    graph TD
        Update["Входящее обновление"] --> OuterStart["Outer Middleware (начало)"]
        OuterStart --> Router["Поиск обработчика"]
        Router --> Filters{"Фильтры"}
        Filters -- Успех --> InnerStart["Inner Middleware (начало)"]
        InnerStart --> Handler["Вызов обработчика"]
        Handler --> InnerEnd["Inner Middleware (конец)"]
        InnerEnd --> OuterEnd["Outer Middleware (конец)"]
        Filters -- Неудачно --> NextHandler["Следующий обработчик/Роутер"]

Регистрация
-----------

Мидлвари регистрируются на уровне роутера или диспетчера для конкретного типа событий через соответствующие методы ``.middleware.outer()`` и ``.middleware.inner()``.

.. code-block:: python

    # Глобальная внешняя мидлварь для всех сообщений
    dispatcher.message_created.middleware.outer(LoggingMiddleware())

    # Внутренняя мидлварь для callback-кнопок в конкретном роутере
    shop_router.message_callback.middleware.inner(TransactionMiddleware())

Для совместимости с привычками из ``aiogram`` есть короткие формы. Вызов ``.middleware(...)`` добавляет **inner**-мидлварь, ``.outer_middleware(...)`` - **outer**. Метод ``.register(...)`` делает то же самое и возвращает саму мидлварь.

.. code-block:: python

    dispatcher.message_created.middleware(TransactionMiddleware())  # inner
    dispatcher.message_created.outer_middleware(LoggingMiddleware())  # outer

    middleware = dispatcher.message_created.middleware.register(TransactionMiddleware())

Вызов без аргументов возвращает декоратор - как в ``aiogram``. Скобки обязательны.
Декорировать нужно готовый объект мидлвари или функцию с той же сигнатурой,
а не класс.

.. code-block:: python

    @dispatcher.message_created.outer_middleware()
    async def logging_middleware(
        update: MessageCreated,
        ctx: Ctx,
        next: NextMiddleware[MessageCreated],
    ) -> Any:
        return await next(ctx)

Написание своей мидлвари
------------------------

Мидлварь - это класс, наследующий ``BaseMiddleware`` и реализующий асинхронный метод ``__call__``.

.. code-block:: python

    from typing import Any

    from maxo.routing.ctx import Ctx
    from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
    from maxo.types import MessageCreated

    class MyMiddleware(BaseMiddleware[MessageCreated]):
        async def __call__(
            self,
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            # Код, выполняемый ДО обработчика
            print("Before handler")

            # Передача управления следующей мидлвари или обработчику
            result = await next(ctx)

            # Код, выполняемый ПОСЛЕ обработчика
            print("After handler")

            return result
