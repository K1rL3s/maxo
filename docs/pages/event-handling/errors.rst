Обработка ошибок
================

В процессе работы бота могут возникать исключения (ошибки в коде, недоступность внешних сервисов, ошибки валидации). **maxo** предоставляет встроенный механизм для их перехвата и обработки, чтобы ваш бот не падал при возникновении проблем.

Как это работает
----------------

``Dispatcher`` автоматически регистрирует глобальную мидлварь ``ErrorMiddleware``. Она оборачивает процесс обработки каждого события в блок ``try...except``.
Если в любом из хендлеров или мидлварей возникает необработанное исключение (наследуемое от ``Exception``), оно перехватывается, и создается новое событие типа :class:`~maxo.types.error_event.ErrorEvent`.

Это событие затем отправляется в диспетчер, где вы можете поймать его с помощью специальных обработчиков ошибок.

``ErrorMiddleware`` оборачивает только обработку обновлений. Исключения из обработчиков сигналов (``before_startup``, ``after_startup``, ``before_shutdown``, ``after_shutdown``) сюда не попадают и доходят до кода, который запустил бота, - подробнее в :doc:`signals`.

Регистрация обработчика
-----------------------

Для перехвата ошибок используется декоратор ``@router.error()`` (или ``@dispatcher.error()``).

.. code-block:: python

    from typing import Any

    from maxo.types import ErrorEvent

    @router.error()
    async def global_error_handler(event: ErrorEvent[Exception, Any]):
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
    from maxo.types import ErrorEvent, MessageCreated

    # Перехват ошибок конкретного типа
    @router.error(ExceptionTypeFilter(ValueError))
    async def value_error_handler(event: ErrorEvent[ValueError, MessageCreated]):
        # event.event - исходный апдейт, у него есть методы фасада
        await event.event.answer_text("Вы ввели некорректные данные!")


ExceptionMessageFilter
~~~~~~~~~~~~~~~~~~~~~~

Фильтрует ошибки по тексту сообщения (поддерживает регулярные выражения).

.. code-block:: python

    from typing import Any

    from maxo.routing.filters import ExceptionMessageFilter
    from maxo.types import ErrorEvent

    @router.error(ExceptionMessageFilter(r"Access denied"))
    async def access_denied_handler(event: ErrorEvent[Exception, Any]):
        ...

Аргументы обработчика
---------------------

В обработчик ошибки передаются следующие аргументы:

1.  **event**: объект :class:`~maxo.types.error_event.ErrorEvent`. Содержит:

    - ``event.exception`` (алиас ``event.error``) - само исключение.
    - ``event.event`` - исходное событие (Update), при обработке которого возникла
      ошибка. У него доступны методы фасада, например ``answer_text``.
    - ``event.update`` - обёртка ``MaxoUpdate`` над исходным событием, с маркером
      апдейта. Само событие лежит в ``event.update.update``.

    ``ErrorEvent`` параметризуется типами исключения и апдейта:
    ``ErrorEvent[MyCustomError, MessageCreated]``.
2.  **ctx**: контекст выполнения.
3.  Либо "заинлайненные" ключи **ctx**

Пример
------

.. code-block:: python

    import logging

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import ExceptionTypeFilter
    from maxo.types import ErrorEvent, MessageCreated, UpdateContext

    class MyCustomError(Exception):
        pass

    @router.message_created()
    async def my_handler(update: MessageCreated, ctx: Ctx):
        if update.message.body.text == "boom":
            raise MyCustomError("Ба-бах!")

    @router.error(ExceptionTypeFilter(MyCustomError))
    async def error_handler(
        event: ErrorEvent[MyCustomError, MessageCreated],
        update_context: UpdateContext,
    ):
        # Пытаемся отправить сообщение в тот же чат, где произошла ошибка.
        # chat_id из update_context может быть None - тогда отвечаем через фасад
        chat_id = update_context.chat_id
        text = f"Ой, что-то сломалось: {event.exception}"
        try:
            if chat_id is None:
                await event.event.answer_text(text)
            else:
                await event.bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            # Если не удалось отправить сообщение об ошибке, просто логируем
            logging.exception("Не удалось отправить уведомление об ошибке")
