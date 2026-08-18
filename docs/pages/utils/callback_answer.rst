Авто-ответ на колбэк
====================

``CallbackAnswerMiddleware`` отвечает на ``MessageCallback`` после нажатия
инлайн-кнопки.

Подключение
-----------

Мидлварь регистрируется как внутренняя (inner) на обсёрвере
``message_callback``:

.. code-block:: python

    from maxo import Dispatcher
    from maxo.utils.callback_answer import CallbackAnswerMiddleware

    dp = Dispatcher()
    dp.message_callback.middleware(CallbackAnswerMiddleware())

По умолчанию middleware отвечает пустым ответом **после** хендлера. Ответ
отправляется даже если хендлер бросил исключение.

Настройка через флаги
---------------------

Флаг ``callback_answer`` переопределяет параметры конструктора для конкретного
хендлера. Подробнее о флагах: :doc:`../event-handling/flags`.

.. code-block:: python

    from maxo import flags
    from maxo.types import MessageCallback


    @dp.message_callback()
    @flags.callback_answer(notification="Готово!")
    async def handler(update: MessageCallback) -> None: ...


    @dp.message_callback()
    @flags.callback_answer(disabled=True)  # отвечаем на колбэк сами
    async def manual_handler(update: MessageCallback) -> None: ...

Словарь принимает ключи ``disabled``, ``before`` и ``notification``. Декоратор
без аргументов включает авто-ответ для мидлвари с ``disabled=True``. Значение
``False`` отключает авто-ответ для одного хендлера.

Управление из хендлера
----------------------

Мидлварь сохраняет изменяемый ``CallbackAnswer`` в ``ctx`` под ключом
``callback_answer``. Хендлер может принять этот объект одноимённым параметром и
изменить настройки до отправки ответа:

.. code-block:: python

    from maxo.types import MessageCallback
    from maxo.utils.callback_answer import CallbackAnswer


    @dp.message_callback()
    async def handler(
        update: MessageCallback,
        callback_answer: CallbackAnswer,
    ) -> None:
        callback_answer.notification = "Готово!"
        # callback_answer.disable()               # не отвечать вовсе

После отправки ответа ``CallbackAnswer`` становится неизменяемым. Попытка
записать любое поле вызывает ``CallbackAnswerException``.

.. automodule:: maxo.utils.callback_answer
   :members:
   :undoc-members:
   :show-inheritance:
