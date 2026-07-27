Диспетчер и роутеры
===================

В основе обработки событий в **maxo** лежит механизм маршрутизации, который позволяет гибко управлять потоком входящих обновлений.

Диспетчер (Dispatcher)
----------------------

``Dispatcher`` - корневой роутер вашего бота. Он отвечает за получение обновлений (через Long Polling или Webhook) и их распределение по цепочке обработчиков. Диспетчер также инициализирует хранилище состояний (FSM) и глобальные middleware.

.. code-block:: python

    import os

    from maxo import Bot, Dispatcher
    from maxo.routing.ctx import Ctx
    from maxo.types import MessageCreated

    bot = Bot(token=os.environ["TOKEN"])
    dispatcher = Dispatcher()

    # Регистрация обработчиков прямо в диспетчере (так как он тоже Router)
    @dispatcher.message_created()
    async def echo(update: MessageCreated, ctx: Ctx):
        await update.answer_text(update.message.body.text or "Текста нет")

    # Запуск
    dispatcher.run_polling(bot)

Роутеры (Routers)
-----------------

``Router`` позволяет структурировать код бота, разбивая его на логические модули (например, «админка», «магазин», «техподдержка»). Вместо того чтобы регистрировать все обработчики в одном файле, вы можете разнести их по разным роутерам.

Вы можете создавать сколько угодно роутеров и вкладывать их друг в друга. Событие проходит по роутерам в порядке их регистрации.

.. code-block:: python

    from maxo import Router

    admin_router = Router(name="admin")
    shop_router = Router(name="shop")

    # Регистрация обработчиков в роутерах
    @admin_router.message_created(...)
    async def admin_handler(...): ...

    @shop_router.message_created(...)
    async def shop_handler(...): ...

    # Подключение роутеров к диспетчеру
    dispatcher.include(admin_router)
    dispatcher.include(shop_router)

Вложенность
-----------

Роутеры могут быть вложенными. Это позволяет создавать сложные иерархии обработки. Например, у вас может быть главный роутер для диалогов, который включает в себя под-роутеры для разных сценариев.

.. code-block:: python

    settings_router = Router()
    profile_router = Router()

    # Роутер профиля включает в себя роутер настроек
    profile_router.include(settings_router)

    # Диспетчер включает роутер профиля
    dispatcher.include(profile_router)

Фильтры на уровне роутера
--------------------------

Помимо фильтров на отдельных обработчиках, вы можете установить **фильтр на целый роутер** (точнее - на его наблюдатель за конкретным типом события).

Если фильтр роутера не проходит, **все** обработчики этого типа в данном роутере будут пропущены, и событие перейдёт к следующему роутеру.

.. code-block:: python

    from maxo import Router
    from maxo.enums import ChatType
    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import BaseFilter
    from maxo.types import MessageCreated

    class IsGroupChat(BaseFilter[MessageCreated]):
        """Пропускает только сообщения из групповых чатов."""
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            return update.message.recipient.chat_type == ChatType.CHAT

    # Создаём роутер и навешиваем фильтр на все его message_created обработчики
    group_router = Router(name="group")
    group_router.message_created.filter(IsGroupChat())

    @group_router.message_created()
    async def group_handler(update: MessageCreated, ctx: Ctx):
        # Этот обработчик вызовется ТОЛЬКО для групповых чатов
        await update.answer_text("Привет, группа!")

    @group_router.message_created()
    async def another_group_handler(update: MessageCreated, ctx: Ctx):
        # Этот обработчик тоже только для групповых чатов
        ...

.. note::

   Метод ``.filter()`` устанавливается на наблюдатель конкретного типа события
   (например, ``message_created``, ``message_callback``). Это позволяет гибко
   управлять маршрутизацией: один роутер может обрабатывать только события из
   групп, другой - только из личных сообщений. В ``.filter()`` можно передать
   несколько фильтров - они будут объединены по правилу ``И``.

Порядок обработки
-----------------

Когда приходит событие (например, новое сообщение), оно проверяется на соответствие фильтрам обработчиков в каждом роутере по очереди:

1.  Сначала проверяются обработчики ``dispatcher``.
2.  Затем проверяются вложенные роутеры в том порядке, в котором они были подключены через ``include()``.
3.  Внутри каждого роутера обработчики проверяются в порядке их определения в коде.

Если обработчик найден и все фильтры прошли успешно, событие обрабатывается, и дальнейшее распространение останавливается.
Если ни один обработчик в текущем роутере не подошел, управление передается следующему роутеру в списке.

Пример: приоритет обработчиков
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from maxo import Dispatcher, Router
    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated

    dispatcher = Dispatcher()
    admin_router = Router(name="admin")
    user_router = Router(name="user")

    # 1. Обработчик диспетчера - проверяется ПЕРВЫМ
    @dispatcher.message_created(Command("start"))
    async def global_start(update: MessageCreated, ctx: Ctx):
        await update.answer_text("Глобальный /start")

    # 2. Обработчик в admin_router - проверяется ВТОРЫМ
    @admin_router.message_created(Command("start"))
    async def admin_start(update: MessageCreated, ctx: Ctx):
        # Этот обработчик НЕ будет вызван для /start,
        # потому что глобальный обработчик уже перехватил событие
        await update.answer_text("Админский /start")

    # 3. Обработчик в user_router - проверяется ТРЕТЬИМ
    @user_router.message_created()
    async def echo(update: MessageCreated, ctx: Ctx):
        # Обрабатывает всё, что не было перехвачено выше
        await update.answer_text(update.message.body.text or "Текста нет")

    # Порядок подключения определяет приоритет между роутерами
    dispatcher.include(admin_router)  # admin_router проверяется раньше
    dispatcher.include(user_router)  # user_router проверяется позже

Доступные события
-----------------

Ниже приведен список всех событий, которые вы можете перехватывать и обрабатывать с помощью диспетчера и роутеров.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Декоратор регистрации
     - Тип события (Update)
     - Описание
   * - ``@router.message_created``
     - :class:`~maxo.types.message_created.MessageCreated`
     - Новое сообщение от пользователя (текст, фото, файлы и т.д.).
   * - ``@router.message_callback``
     - :class:`~maxo.types.message_callback.MessageCallback`
     - Нажатие на кнопку Inline-клавиатуры.
   * - ``@router.message_edited``
     - :class:`~maxo.types.message_edited.MessageEdited`
     - Пользователь отредактировал ранее отправленное сообщение.
   * - ``@router.message_removed``
     - :class:`~maxo.types.message_removed.MessageRemoved`
     - Пользователь удалил сообщение.
   * - ``@router.bot_started``
     - :class:`~maxo.types.bot_started.BotStarted`
     - Пользователь нажал кнопку «Запустить» или впервые начал диалог с ботом.
   * - ``@router.bot_stopped``
     - :class:`~maxo.types.bot_stopped.BotStopped`
     - Пользователь заблокировал бота.
   * - ``@router.user_added_to_chat``
     - :class:`~maxo.types.user_added_to_chat.UserAddedToChat`
     - В групповой чат добавлен новый участник.
   * - ``@router.user_removed_from_chat``
     - :class:`~maxo.types.user_removed_from_chat.UserRemovedFromChat`
     - Участник покинул групповой чат или был удален.
   * - ``@router.bot_added_to_chat``
     - :class:`~maxo.types.bot_added_to_chat.BotAddedToChat`
     - Бот добавлен в групповой чат.
   * - ``@router.bot_removed_from_chat``
     - :class:`~maxo.types.bot_removed_from_chat.BotRemovedFromChat`
     - Бот удален из группового чата.
   * - ``@router.chat_title_changed``
     - :class:`~maxo.types.chat_title_changed.ChatTitleChanged`
     - Название группового чата изменено.
   * - ``@router.dialog_cleared``
     - :class:`~maxo.types.dialog_cleared.DialogCleared`
     - История переписки очищена.
   * - ``@router.dialog_removed``
     - :class:`~maxo.types.dialog_removed.DialogRemoved`
     - Диалог удален.
   * - ``@router.dialog_muted`` / ``@router.dialog_unmuted``
     - :class:`~maxo.types.dialog_muted.DialogMuted` / :class:`~maxo.types.dialog_unmuted.DialogUnmuted`
     - Уведомления в диалоге отключены или включены.
   * - ``@router.error``
     - :class:`~maxo.types.error_event.ErrorEvent`
     - Произошла ошибка при обработке другого события.

Сигналы жизненного цикла
~~~~~~~~~~~~~~~~~~~~~~~~

Эти события не приходят от Max API, а генерируются самим фреймворком при запуске и остановке.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Декоратор регистрации
     - Тип сигнала
     - Описание
   * - ``@router.before_startup``
     - :class:`~maxo.routing.signals.startup.BeforeStartup`
     - Вызывается перед запуском процесса получения обновлений (Polling/Webhook).
   * - ``@router.after_startup``
     - :class:`~maxo.routing.signals.startup.AfterStartup`
     - Вызывается сразу после успешного старта.
   * - ``@router.before_shutdown``
     - :class:`~maxo.routing.signals.shutdown.BeforeShutdown`
     - Вызывается перед началом процесса остановки бота (Graceful Shutdown).
   * - ``@router.after_shutdown``
     - :class:`~maxo.routing.signals.shutdown.AfterShutdown`
     - Вызывается после полной остановки и закрытия соединений.
