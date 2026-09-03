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

    from magic_filter import F

    from maxo.integrations.magic_filter import MagicFilter
    from maxo.types import MessageCreated

    # Обработка команды /admin ИЛИ сообщения с текстом "secret"
    @dispatcher.message_created(Command("admin") | MagicFilter(F.text == "secret"))
    async def admin_area(update: MessageCreated):
        ...

Несколько фильтров через запятую (И)
------------------------------------

При регистрации обработчика можно передать сразу несколько фильтров через
запятую. Они автоматически объединяются по правилу ``И`` (эквивалент ``&``),
поэтому обработчик сработает только если сработали все переданные фильтры.

.. code-block:: python

    from magic_filter import F

    from maxo.integrations.magic_filter import MagicFilter
    from maxo.routing.filters import Command
    from maxo.types import MessageCreated

    # Эти две регистрации эквивалентны
    @dispatcher.message_created(Command("start"), MagicFilter(F.text == "hello"))
    async def start(update: MessageCreated):
        ...

    @dispatcher.message_created(Command("start") & MagicFilter(F.text == "hello"))
    async def start_explicit(update: MessageCreated):
        ...

То же самое работает и для методов ``handler`` и ``register``:

.. code-block:: python

    dispatcher.message_created.handler(
        start,
        Command("start"),
        MagicFilter(F.text == "hello"),
    )
    dispatcher.message_created.register(
        start,
        Command("start"),
        MagicFilter(F.text == "hello"),
    )
    dispatcher.message_created.filter(
        Command("start"),
        MagicFilter(F.text == "hello"),
    )

Magic Filter
------------

Библиотека интегрирована с ``magic_filter``. Это позволяет писать выразительные условия прямо в коде, обращаясь к атрибутам обновления через объект ``F``.

.. code-block:: python

    from magic_filter import F

    from maxo.integrations.magic_filter import MagicFilter
    from maxo.routing.ctx import Ctx
    from maxo.types import MessageCreated

    # Сработает, если текст сообщения равен "hello"
    @dispatcher.message_created(MagicFilter(F.text == "hello"))
    async def hello(update: MessageCreated, ctx: Ctx):
        ...

    # Сработает, если у отправителя имя "Kirill"
    @dispatcher.message_created(MagicFilter(F.message.sender.first_name == "Kirill"))
    async def kirill_handler(update: MessageCreated, ctx: Ctx):
        ...

.. warning::

    При объединении сравнений через ``|`` или ``&`` каждое сравнение нужно
    заключать в скобки. Побитовые операторы имеют более высокий приоритет,
    чем ``==``.

    .. code-block:: python

        # Неправильно: Python сначала вычислит "hello" | F.text
        F.text == "hello" | F.text == "hi"

        # Правильно
        (F.text == "hello") | (F.text == "hi")

        # Для нескольких допустимых значений короче использовать in_
        F.text.in_({"hello", "hi"})

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

.. note::

    Каждый фильтр вычисляется в изоляции: его записи попадают в общий ``ctx``
    только если он вернул ``True``. Это касается и одиночного фильтра, и целой
    цепочки. Если фильтр (или цепочка) не прошёл, его записи отбрасываются и не
    видны следующим хендлерам и роутерам.

    Изоляция работает на уровне ключей, поэтому фильтр должен именно
    переприсваивать их (``ctx["command"] = ...``). Копия контекста
    поверхностная: мутация вложенного объекта на месте
    (``ctx["data"].append(...)``) переживёт откат, а удаление ключа
    (``del ctx["command"]``) не применится даже при прохождении фильтра.

    Правила для составных фильтров:

    - ``И`` (``&``, ``AndFilter``) - атомарна: записи всех фильтров цепочки
      применяются только при её полном прохождении, при первом же ``False`` всё
      откатывается.
    - ``ИЛИ`` (``|``, ``OrFilter``) - применяются записи только первой прошедшей
      ветки; записи непрошедших веток отбрасываются.
    - Инверсия (``~``, ``InvertFilter``) - не пропускает записи вложенного
      фильтра, ведь она проходит именно тогда, когда тот не прошёл. Цепочка
      инверсий схлопывается по чётности: ``~~f`` равнозначна самому ``f`` и
      переносит его записи в ``ctx``, а ``~~~f`` - обычной ``~f``.

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
