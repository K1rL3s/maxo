Фильтры
=======

Фильтры в **maxo** позволяют отсеивать события, которые вы хотите обрабатывать. Это один из ключевых механизмов маршрутизации.
Вместо того чтобы писать один большой ``if/else`` внутри обработчика, вы декларируете условия срабатывания прямо в декораторе.

.. code-block:: python

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated

    @dispatcher.message_created(Command("start"))
    async def start(update: MessageCreated, ctx: Ctx):
        ...

Встроенные фильтры
------------------

**maxo** поставляется с набором готовых фильтров:

- ``Command`` - проверяет команду (например, ``/start`` или ``/help``).
- ``StateFilter`` - фильтрует по текущему состоянию FSM (например, ``StateFilter(MyStates.waiting_name)``).
- ``MagicFilter`` - инструмент для создания условий на лету (см. ниже).
- ``SyncFilter`` - оборачивает синхронную функцию-предикат, чтобы её можно было использовать как фильтр (см. ниже).

Комбинирование (Логические операции)
------------------------------------

Вы можете комбинировать фильтры с помощью логических операторов ``&`` (И), ``|`` (ИЛИ) и ``~`` (НЕ).

.. code-block:: python

    from maxo.integrations.magic_filter import F
    from maxo.types import MessageCreated

    # Обработка команды /admin ИЛИ сообщения с текстом "secret"
    @dispatcher.message_created(Command("admin") | (F.text == "secret"))
    async def admin_area(update: MessageCreated):
        ...

Несколько фильтров через запятую (И)
------------------------------------

При регистрации обработчика можно передать сразу несколько фильтров через
запятую. Они автоматически объединяются по правилу ``И`` (эквивалент ``&``),
поэтому обработчик сработает только если сработали все переданные фильтры.

.. code-block:: python

    from maxo.integrations.magic_filter import F
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated

    # Эти две регистрации эквивалентны
    @dispatcher.message_created(Command("start"), F.text == "hello")
    async def start(update: MessageCreated):
        ...

    @dispatcher.message_created(Command("start") & (F.text == "hello"))
    async def start_explicit(update: MessageCreated):
        ...

То же самое работает и для методов ``handler`` и ``register``:

.. code-block:: python

    dispatcher.message_created.handler(
        start,
        Command("start"),
        F.text == "hello",
    )
    dispatcher.message_created.register(
        start,
        Command("start"),
        F.text == "hello",
    )
    dispatcher.message_created.filter(
        Command("start"),
        F.text == "hello",
    )

Magic Filter
------------

Библиотека интегрирована с ``magic_filter``. Это позволяет писать выразительные условия прямо в коде, обращаясь к атрибутам обновления через объект ``F``. Импортируйте его из интеграции - обычный ``F`` из пакета ``magic_filter`` фильтром **maxo** не является.

.. code-block:: python

    from maxo.integrations.magic_filter import F
    from maxo.routing.ctx import Ctx
    from maxo.types import MessageCreated

    # Сработает, если текст сообщения равен "hello"
    @dispatcher.message_created(F.text == "hello")
    async def hello(update: MessageCreated, ctx: Ctx):
        ...

    # Сработает, если у отправителя имя "Kirill"
    @dispatcher.message_created(F.message.sender.first_name == "Kirill")
    async def kirill_handler(update: MessageCreated, ctx: Ctx):
        ...

Фильтром является **любой** узел магии, а не только результат сравнения: ``F.text`` (в значении «есть текст») - такой же фильтр, как ``F.text == "hello"``. Как фильтр магия резолвится по апдейту, а результат приводится к ``bool``.

.. code-block:: python

    # Сработает на любом сообщении с текстом
    @dispatcher.message_created(F.message.body.text)
    async def any_text(update: MessageCreated):
        ...

    # Цепочки собираются как обычно
    @dispatcher.message_created(F.text.casefold() == "отмена")
    async def cancel(update: MessageCreated):
        ...

    @dispatcher.message_created(F.text.regexp(r"^\d+$"))
    async def digits(update: MessageCreated):
        ...

Магия комбинируется и с магией, и с обычными фильтрами **maxo**:

.. code-block:: python

    @dispatcher.message_created((F.text == "да") | (F.text == "нет"))
    async def answer(update: MessageCreated):
        ...

    @dispatcher.message_created(Command("start") & F.message.body.text)
    async def start_with_text(update: MessageCreated):
        ...

Если результат магии нужен в обработчике, задайте ``result_key`` - значение доедет до него как аргумент:

.. code-block:: python

    from maxo.integrations.magic_filter import F, MagicData, MagicFilter

    @dispatcher.message_created(MagicFilter(F.message.body.text, result_key="text"))
    async def with_text(update: MessageCreated, text: str):
        ...

``MagicData`` работает так же, но резолвит магию не по апдейту, а по контексту.

Магия из интеграции подходит и диалогам: это полноценный ``magic_filter``, поэтому ее можно передавать в ``when`` виджетов ``maxo.dialogs``.

.. code-block:: python

    from maxo.dialogs.widgets.text import Format
    from maxo.integrations.magic_filter import F

    Format("Выбрано: {selected}", when=F["selected"])
    Format("Ничего не выбрано", when=~F["selected"])

SyncFilter (синхронные предикаты)
---------------------------------

Фильтры в **maxo** асинхронные, поэтому обычную синхронную функцию или лямбду нельзя передать в декоратор напрямую.
``SyncFilter`` оборачивает синхронный предикат ``Callable[[Update], bool]`` и зовёт его в асинхронном ``__call__``.

.. code-block:: python

    from maxo.routing.filters import SyncFilter
    from maxo.types import MessageCreated

    @dispatcher.message_created(SyncFilter(lambda u: u.message.body.text == "ping"))
    async def ping(update: MessageCreated):
        ...

По умолчанию ошибка предиката трактуется как ``False`` (флаг ``exceptions_as_false``), чтобы битый предикат не ронял обработку апдейта.
Для блокирующих функций передайте ``run_in_thread=True`` - вызов уйдёт в ``asyncio.to_thread``.
Операторы ``& | ~`` наследуются от ``BaseFilter``.

Создание своих фильтров
-----------------------

Фильтр - это любой вызываемый объект (callable), принимающий ``update`` и возвращающий ``bool`` (или ``Awaitable[bool]``).
Если фильтру нужно передать данные обработчику, он может сохранить их напрямую в словарь ``ctx``, так как контекст является мутабельным и общим для всего цикла обработки.

.. code-block:: python

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import BaseFilter
    from maxo.types import MessageCreated

    class MyFilter(BaseFilter[MessageCreated]):
        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            return update.message.body.text == "foo"

Пример: фильтр с параметром и пробросом данных
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Фильтр может принимать аргументы конструктора и складывать промежуточные вычисления в ``ctx``:

.. code-block:: python

    from maxo.routing.ctx import Ctx
    from maxo.routing.filters import BaseFilter
    from maxo.types import MessageCreated

    class MinLengthFilter(BaseFilter[MessageCreated]):
        """Пропускает сообщения длиннее min_length символов."""

        def __init__(self, min_length: int):
            self.min_length = min_length

        async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
            text = update.message.body.text or ""
            if len(text) >= self.min_length:
                # Сохраняем вычисленное значение в контекст
                ctx["text_length"] = len(text)
                return True
            return False

    @router.message_created(MinLengthFilter(10))
    async def long_message_handler(
        update: MessageCreated,
        ctx: Ctx,
        text_length: int,
    ):
        await update.answer_text(f"Длинное сообщение! ({text_length} символов)")
