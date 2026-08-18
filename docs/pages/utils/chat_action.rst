Действия бота в чате
====================

.. meta::
   :description: ChatActionSender и ChatActionMiddleware в maxo для повторной
      отправки действий бота во время долгих операций.
   :keywords: maxo chat action, ChatActionSender, ChatActionMiddleware, typing_on

MAX показывает действие бота (``typing_on``, ``sending_photo`` и другие) только
некоторое время. ``ChatActionSender`` повторяет его в фоновой задаче, пока идёт
долгая операция.

Отправщик
---------

``ChatActionSender`` - асинхронный контекстный менеджер. Пока выполняется код
внутри ``async with``, он отправляет действие каждые ``interval`` секунд.

.. code-block:: python

    from maxo import Bot
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated
    from maxo.utils.chat_action import ChatActionSender


    @dp.message_created(Command("report"))
    async def report_handler(update: MessageCreated, bot: Bot) -> None:
        async with ChatActionSender.typing_on(bot=bot, chat_id=update.chat_id):
            result = await build_long_report()

        await update.answer(text=result)

Для стандартных действий есть методы ``typing_on``, ``sending_photo``,
``sending_video``, ``sending_audio``, ``sending_file`` и ``mark_seen``.
Параметр ``action`` позволяет задать действие напрямую:

.. code-block:: python

    from maxo.enums import SenderAction

    async with ChatActionSender(
        bot=bot,
        chat_id=chat_id,
        action=SenderAction.SENDING_FILE,
        interval=3,  # как часто переотправлять действие
        initial_sleep=1,  # не мигать действием, если работа окажется быстрой
    ):
        ...

Мидлварь
--------

``ChatActionMiddleware`` запускает отправщик для выбранного хендлера, поэтому
писать ``async with`` в каждом хендлере не нужно. Мидлварь регистрируется как
**внутренняя** (inner), где доступны флаги хендлера:

.. code-block:: python

    from maxo.utils.chat_action import ChatActionMiddleware

    dp.message_created.middleware(ChatActionMiddleware())

После регистрации хендлеры дольше ``initial_sleep`` будут показывать
``typing_on``.

Параметры отправщика по умолчанию задаются в конструкторе мидлвари. Ненулевой
``initial_sleep`` не запускает отправку для быстрых хендлеров и экономит один
запрос к API:

.. code-block:: python

    dp.message_created.middleware(ChatActionMiddleware(initial_sleep=1))

Настройка через флаги
---------------------

Флаг ``chat_action`` переопределяет настройки для конкретного хендлера.
Подробнее о флагах: :doc:`../event-handling/flags`.

Строка или ``SenderAction`` задаёт действие:

.. code-block:: python

    from maxo import flags
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated


    @dp.message_created(Command("photo"))
    @flags.chat_action("sending_photo")
    async def my_handler(update: MessageCreated) -> None: ...

Словарь задаёт несколько параметров отправщика:

.. code-block:: python

    @dp.message_created(Command("file"))
    @flags.chat_action(action="sending_file", interval=3, initial_sleep=1)
    async def my_handler(update: MessageCreated) -> None: ...

Значение ``False`` отключает отправку:

.. code-block:: python

    @dp.message_created(Command("fast"))
    @flags.chat_action(False)
    async def my_handler(update: MessageCreated) -> None: ...

Мидлварь берёт ID чата из ``update_context`` в ``ctx`` или из самого апдейта.
Если ID найти не удалось, мидлварь вызывает хендлер без отправки действия.

Справочник
----------

.. automodule:: maxo.utils.chat_action
   :members:
   :undoc-members:
   :show-inheritance:
