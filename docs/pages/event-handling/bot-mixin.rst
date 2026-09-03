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

``as_(bot)`` внедряет бота в объект и всё дерево внутри него, а возвращает его же
(``self``), что позволяет использовать fluent-стиль:

.. code-block:: python

    profile = UserProfile(user_id=1, name="Alice").as_(bot)
    await profile.notify("Привет!")

Присваивание ``profile.bot = bot`` делает то же самое: вложенные объекты получают
бота вместе с корнем, вручную спускаться к полям не нужно.

Привязка бота при десериализации
---------------------------------

Реторта одна на процесс и о боте ничего не знает, а привязка делается
явным шагом - :func:`~maxo.types.bind_bot`. Он проставляет ``_bot`` только
тем типам, которым он нужен: у которых есть методы-фасады
(``message.answer()`` и подобные), и спускается к ним по полям.

.. code-block:: python

    from maxo import get_retort
    from maxo.types import Updates, bind_bot

    update = bind_bot(get_retort().load(data, Updates), bot)

    assert update.bot is bot
    assert update.message.bot is bot

В обычном коде звать ``bind_bot`` не нужно - его делают за вас: ``Bot.call_method``
привязывает ответы методов, а вебхук и лонг-поллинг - входящие апдейты.

.. note::

   ``BotMixin`` есть у типов с методами-фасадами (``message.answer()`` и
   подобные) и у типов, внутри которых такие лежат: ``ChatList``, ``UpdateList``,
   ``SendMessageResult`` и прочих контейнеров. Поэтому ``chat_list.bot = bot``
   работает и спускает бота до вложенных сообщений.

   У листьев без фасадов (``User``, ``MessageBody``, ``Recipient``) свойства
   ``.bot`` нет - обращение упадёт с обычным ``AttributeError``. Если бот нужен
   вашему собственному типу, унаследуйтесь от ``BotMixin`` явно (см. ниже).

Прогрев
-------

Компиляция загрузчиков и дамперов ленивая. :func:`~maxo.bot.warming_up.warm_up` переносит эту цену в
инициализацию процесса:

.. code-block:: python

    import maxo
    from maxo.bot.methods import SendMessage
    from maxo.types import Updates

    # в глобальной области модуля, а не в хендлере
    maxo.warm_up(loaded=[Updates], dumped=[SendMessage])

``Bot(warming_up=True)`` делает то же самое (это поведение по умолчанию, как и
раньше), но греет всё подряд. Список стоит сузить: задержка первого запроса
будет той же, а инициализация - втрое короче.

Создание собственных миксинов
------------------------------

Если вы хотите добавить функциональность бота только к отдельным типам, не используя ``MaxoType``,
можно унаследоваться напрямую от ``BotMixin``:

.. code-block:: python

    from maxo.types import BaseMaxoType, BotMixin

    class LightType(BaseMaxoType, BotMixin):
        value: int

.. note::

   ``bind_bot`` спускается только в те поля, где по типам может встретиться
   ``BotMixin``. Собственный тип он найдёт, если тот лежит в дереве загруженного
   объекта; отдельно созданному вызывайте ``as_(bot)`` вручную.

API
---

.. autoclass:: maxo.types.BotMixin
   :members:
   :undoc-members:
   :no-index:

.. autoclass:: maxo.types.BaseMaxoType
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:


.. autoclass:: maxo.types.MaxoType
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
