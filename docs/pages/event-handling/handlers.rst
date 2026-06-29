Обработчики и аргументы
=======================

Обработчик (handler, хэндлер) - это асинхронная функция, которая выполняется в ответ на входящее событие (Update), прошедшее через все фильтры.

Регистрация
-----------

Обработчики регистрируются через декораторы на роутере или диспетчере. В декоратор можно передать один или несколько фильтров.

.. code-block:: python

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import Command, CommandStart
    from maxo.routing.updates import MessageCreated

    # Оба варианта эквивалентны:
    @router.message_created(CommandStart())
    # или
    # @router.message_created(Command("start"))
    async def my_handler(update: MessageCreated, ctx: Ctx):
        ...

Аргументы
---------

**maxo** автоматически внедряет аргументы в функцию-обработчик на основе их имен (ключей в ``ctx``). Основные доступные аргументы:

1.  **Объект обновления** (первый позиционный аргумент): типизированный объект события, например ``MessageCreated``, ``MessageCallback``. Содержит все данные, пришедшие от API.
2.  ``ctx: Ctx`` - контекст выполнения. Словарь-подобный объект, который живет в рамках обработки одного обновления. В нем хранятся ссылки на ``bot``, ``update``, а также любые данные, добавленные мидлварями.
3.  ``facade: Facade`` - обёртка над обновлением. Подробнее в разделе :doc:`facades`.
4.  ``fsm_context: FSMContext`` - контекст конечного автомата (FSM). Доступен, если FSM активирован. Подробнее в разделе :doc:`fsm`.

.. code-block:: python

    from maxo.routing.ctx import Ctx
    from maxo.routing.updates import MessageCreated

    @router.message_created()
    async def echo(update: MessageCreated, ctx: Ctx):
        await update.answer_text(update.message.body.text or "Текста нет")

Dependency Injection (DI)
-------------------------

Вы можете передавать произвольные данные в обработчики через фильтры и мидлвари.

1.  **Через фильтры**: если фильтр изменяет ``ctx``, эти данные будут добавлены в аргументы обработчика.
2.  **Через мидлвари**: мидлварь может изменить ``ctx``, добавляя новые значения.

.. code-block:: python

    from maxo import Bot
    from maxo.routing.ctx import Ctx
    from maxo.routing.facades import MessageCreatedFacade
    from maxo.routing.filters import BaseFilter
    from maxo.routing.updates import MessageCreated


    # Пример фильтра, который возвращает данные пользователя
    class UserFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            sender = update.message.sender
            if sender is None:
                return False

            user = await get_user_from_db(sender.user_id)
            if user:
                ctx["user"] = user  # Передаем user в обработчик
                return True
            return False

    @router.message_created(UserFilter())
    async def handler(update: MessageCreated, user: User, ctx: Ctx):
        # Аргумент user будет автоматически передан из фильтра
        bot: Bot = ctx["bot"]
        await bot.send_message(user.user_id, f"Hello, {user.first_name}!")

Возвращаемые значения
---------------------

Обычно обработчики ничего не возвращают (``None``). Однако вы можете вернуть специальные значения для управления потоком (например, ``UNHANDLED`` для пропуска обработки, или вызвать исключение ``SkipHandler``).
