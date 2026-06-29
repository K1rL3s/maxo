Инъекция бота в типы (BotMixin)
================================

``BotMixin`` - это mixin, который добавляет в датакласс ссылку на экземпляр бота.
Все типы, наследующие ``MaxoType``, автоматически получают эту функциональность, так как ``MaxoType`` уже включает ``BotMixin``.

Зачем это нужно?
----------------

Иногда удобно, чтобы десериализованный объект сам мог обращаться к боту - например,
для выполнения API-вызовов прямо из метода типа. Благодаря ``BotMixin`` вам не нужно
вручную пробрасывать ``bot`` через аргументы каждого метода.

.. code-block:: python

    from maxo.types import MaxoType

    class UserProfile(MaxoType):
        user_id: int
        name: str

        async def notify(self, text: str) -> None:
            await self.bot.send_message(chat_id=self.user_id, text=text)

Свойство ``bot``
----------------

``BotMixin`` добавляет свойство ``bot``, которое возвращает экземпляр :class:`~maxo.Bot`.

.. code-block:: python

    profile: UserProfile = ...
    bot_instance = profile.bot  # Bot

Если бот не был внедрён, обращение к свойству вызовет :class:`~maxo.errors.AttributeIsEmptyError`:

.. code-block:: python

    from maxo.errors import AttributeIsEmptyError

    profile = UserProfile(user_id=1, name="Alice")

    try:
        _ = profile.bot
    except AttributeIsEmptyError:
        print("Бот не внедрён в объект!")

Метод ``as_``
-------------

``as_(bot)`` внедряет бота в объект и возвращает его же (``self``), что позволяет использовать fluent-стиль:

.. code-block:: python

    profile = UserProfile(user_id=1, name="Alice").as_(bot)
    await profile.notify("Привет!")

Автоматическая инъекция через ретроту
--------------------------------------

Основной сценарий использования ``BotMixin`` - автоматическое внедрение бота при десериализации
через `Retort <https://adaptix.readthedocs.io/>`_. Реторта бота (``bot.retort``) настроена так,
что при загрузке любого ``MaxoType`` бот автоматически присваивается каждому объекту в дереве вложенности.

.. code-block:: python

    from maxo.types import MaxoType

    class Sub(MaxoType):
        value: int

    class MyData(MaxoType):
        name: str
        sub: Sub

    # bot.retort автоматически внедряет бот во все MaxoType-объекты
    data = {"name": "test", "sub": {"value": 42}}
    my = bot.retort.load(data, MyData)

    assert my.bot is bot       # бот внедрён в корневой объект
    assert my.sub.bot is bot   # и во вложенный

Обратная операция - ``dump`` - также работает корректно и не включает поле ``_bot`` в результат:

.. code-block:: python

    result = bot.retort.dump(my, MyData)
    assert result == {"name": "test", "sub": {"value": 42}}

Использование ``create_retort`` вручную
----------------------------------------

Если вы создаёте ретроту самостоятельно через :func:`~maxo.serialization.create_retort`,
передайте ``bot=`` для включения инъекции:

.. code-block:: python

    from maxo.serialization import create_retort

    retort = create_retort(bot=bot)
    my = retort.load(data, MyData)
    assert my.bot is bot

Если ``bot`` не передан (или передан как ``None``), инъекция не производится,
и обращение к ``.bot`` вызовет :class:`~maxo.errors.AttributeIsEmptyError`:

.. code-block:: python

    from maxo.errors import AttributeIsEmptyError

    retort = create_retort()  # bot не передан
    my = retort.load(data, MyData)

    try:
        _ = my.bot
    except AttributeIsEmptyError:
        print("Бот не внедрён!")  # ожидаемое поведение

Создание собственных миксинов
------------------------------

Если вы хотите добавить функциональность бота только к отдельным типам, не используя ``MaxoType``,
можно унаследоваться напрямую от ``BotMixin``:

.. code-block:: python

    from maxo.types import BaseMaxoType, BotMixin

    class LightType(BaseMaxoType, BotMixin):
        value: int

.. note::

   При использовании ``BotMixin`` без ``MaxoType`` инъекция через ``bot.retort`` работает
   только для типов, которые являются подклассами ``MaxoType``. Для ``LightType`` потребуется
   вызвать ``as_(bot)`` вручную.

API
---

.. autoclass:: maxo.types.BotMixin
   :members:
   :undoc-members:

.. autoclass:: maxo.types.BaseMaxoType
   :members:
   :undoc-members:
   :show-inheritance:


.. autoclass:: maxo.types.MaxoType
   :members:
   :undoc-members:
   :show-inheritance:
