Обработка ошибок
================

В процессе работы бота могут возникать исключения (ошибки в коде, недоступность внешних сервисов, ошибки валидации). **maxo** предоставляет встроенный механизм для их перехвата и обработки, чтобы ваш бот не падал при возникновении проблем.

Как это работает
----------------

``Dispatcher`` автоматически регистрирует глобальную мидлварь ``ErrorMiddleware``. Она оборачивает процесс обработки каждого события в блок ``try...except``.
Если в любом из хендлеров или мидлварей возникает необработанное исключение (наследуемое от ``Exception``), оно перехватывается, и создается новое событие типа :class:`~maxo.routing.updates.error.ErrorEvent`.

Это событие затем отправляется в диспетчер, где вы можете поймать его с помощью специальных обработчиков ошибок.

Регистрация обработчика
-----------------------

Для перехвата ошибок используется декоратор ``@router.error()`` (или ``@dispatcher.error()``).

.. code-block:: python

    from maxo.routing.updates import ErrorEvent

    @router.error()
    async def global_error_handler(event: ErrorEvent):
        # Логируем ошибку
        print(f"Произошла ошибка: {event.exception}")
        # Можно попробовать ответить пользователю, если контекст позволяет
        # (но учтите, что update внутри event может быть любым)

Фильтрация ошибок
-----------------

Вы можете фильтровать ошибки по их типу или сообщению, чтобы обрабатывать разные ситуации по-разному.

ExceptionTypeFilter
~~~~~~~~~~~~~~~~~~~

Фильтрует ошибки по классу исключения.

.. code-block:: python

    from maxo.routing.filters import ExceptionTypeFilter
    from maxo.routing.updates import ErrorEvent
    from maxo.types import UpdateContext

    # Перехват ошибок конкретного типа
    @router.error(ExceptionTypeFilter(ValueError))
    async def value_error_handler(
        event: ErrorEvent,
        update_context: UpdateContext,
    ):
        await event.bot.send_message(
            chat_id=update_context.chat_id,
            text="Вы ввели некорректные данные!",
        )


ExceptionMessageFilter
~~~~~~~~~~~~~~~~~~~~~~

Фильтрует ошибки по тексту сообщения (поддерживает регулярные выражения).

.. code-block:: python

    from maxo.routing.filters import ExceptionMessageFilter
    from maxo.routing.updates import ErrorEvent

    @router.error(ExceptionMessageFilter(r"Access denied"))
    async def access_denied_handler(event: ErrorEvent):
        ...

Аргументы обработчика
---------------------

В обработчик ошибки передаются следующие аргументы:

1.  **event**: объект :class:`~maxo.routing.updates.error.ErrorEvent`. Содержит:
    - ``event.exception`` - само исключение.
    - ``event.update`` - исходное событие (Update), при обработке которого возникла ошибка.
2.  **ctx**: контекст выполнения.
3.  Либо "заинлайненные" ключи **ctx**

Пример
------

.. code-block:: python

    import logging

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import ExceptionTypeFilter
    from maxo.routing.updates import ErrorEvent, MessageCreated
    from maxo.types import UpdateContext

    class MyCustomError(Exception):
        pass

    @router.message_created()
    async def my_handler(update: MessageCreated, ctx: Ctx):
        if update.message.body.text == "boom":
            raise MyCustomError("Ба-бах!")

    @router.error(ExceptionTypeFilter(MyCustomError))
    async def error_handler(event: ErrorEvent, update_context: UpdateContext):
        # Пытаемся отправить сообщение в тот же чат, где произошла ошибка
        try:
            await event.bot.send_message(
                chat_id=update_context.chat_id,
                text=f"Ой, что-то сломалось: {event.exception}",
            )
        except Exception:
            # Если не удалось отправить сообщение об ошибке, просто логируем
            logging.exception("Не удалось отправить уведомление об ошибке")
