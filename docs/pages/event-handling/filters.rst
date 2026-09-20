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

**maxo** поставляется с набором готовых фильтров в ``maxo.routing.filters``
(постоянный алиас для портирования с ``aiogram`` - ``maxo.filters``):

- ``Command`` - проверяет команду (например, ``/start`` или ``/help``) и кладёт
  разобранную команду в ``ctx["command"]`` как ``CommandObject``.
- ``CommandStart`` - то же самое, но сразу для ``/start``.
- ``StateFilter`` - фильтрует по текущему состоянию FSM (например, ``StateFilter(MyStates.waiting_name)``).
- ``Payload`` (алиас ``CallbackData``) - типизированный payload инлайн-кнопки (см. ниже).
- ``DeeplinkFilter`` - диплинк в ``BotStarted``; значение попадает в ``ctx`` под
  ключами ``deeplink``, ``payload`` и ``args``.
- ``ExceptionTypeFilter`` и ``ExceptionMessageFilter`` - для обработчиков ошибок,
  см. :doc:`errors`.
- ``SyncFilter`` - оборачивает синхронную функцию-предикат, чтобы её можно было использовать как фильтр (см. ниже).
- ``AlwaysTrueFilter`` и ``AlwaysFalseFilter`` - заглушки, удобные в тестах.
- ``AndFilter``, ``OrFilter``, ``InvertFilter`` и функции ``and_f``, ``or_f``,
  ``invert_f`` - то же, что операторы ``&``, ``|`` и ``~``.
- ``BaseFilter`` - база для своих фильтров (см. ниже).

``MagicFilter`` лежит отдельно, в ``maxo.integrations.magic_filter``, потому что
требует дополнительной зависимости ``maxo[magic_filter]``.

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

Payload (типизированный callback)
---------------------------------

``Payload`` описывает данные инлайн-кнопки как датакласс: ``pack()`` собирает их
в строку payload, а фильтр ``Payload.filter()`` разбирает строку обратно и кладёт
готовый объект в ``ctx["payload"]``. Для привычек из ``aiogram`` есть алиас
``CallbackData``.

.. code-block:: python

    from maxo.routing.filters import Payload
    from maxo.types import MessageCallback, MessageCreated
    from maxo.utils.builders import KeyboardBuilder

    class ItemPayload(Payload, prefix="item"):
        item_id: int
        action: str

    @dispatcher.message_created()
    async def show_item(update: MessageCreated) -> None:
        keyboard = (
            KeyboardBuilder()
            .add_callback(
                text="Купить",
                payload=ItemPayload(item_id=1, action="buy").pack(),
            )
            .build()
        )
        await update.answer_text("Товар", keyboard=keyboard)

    @dispatcher.message_callback(ItemPayload.filter())
    async def on_item(update: MessageCallback, payload: ItemPayload) -> None:
        await update.callback_answer(f"{payload.action}: {payload.item_id}")

``prefix`` обязателен и не должен содержать разделитель (по умолчанию ``":"``,
меняется параметром ``sep``). Поля упаковываются в том же порядке, в каком
объявлены; поддерживаются ``int``, ``str``, ``float``, ``bool``, ``Decimal``,
``Fraction``, ``UUID``, ``Enum`` и их nullable-варианты. Собранный payload
ограничен 1024 байтами - при превышении ``pack()`` кидает ``ValueError``.

В ``filter()`` можно передать дополнительный фильтр, который получит уже
разобранный payload из ``ctx``:

.. code-block:: python

    from magic_filter import F

    from maxo.integrations.magic_filter import MagicData

    # MagicData смотрит в ctx, где уже лежит разобранный payload
    @dispatcher.message_callback(
        ItemPayload.filter(MagicData(F.payload.action == "buy")),
    )
    async def on_buy(update: MessageCallback, payload: ItemPayload) -> None:
        ...

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
