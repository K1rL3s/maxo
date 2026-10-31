Бот внутри типов (FacadeMaxoType)
=================================

Апдейты и сообщения умеют отвечать сами: ``await update.answer("Привет")``.
Для этого они держат ссылку на бота. Остальные типы - ``User``, ``Chat``,
методы API, ``BotDefaults`` - обычные датаклассы без бота.

.. list-table::
   :header-rows: 1

   * - Класс
     - Бот
     - Кто наследует
   * - ``MaxoType``
     - нет
     - все типы API, методы, конфиги
   * - ``FacadeMaxoType``
     - поле ``_bot``, свойство ``bot``, метод ``as_``
     - ``MaxUpdate`` (все апдейты), ``Message``, ``CommentMessage``

Свойство ``bot``
----------------

Возвращает :class:`~maxo.Bot`. Если бот не привязан, кидает
:class:`~maxo.errors.AttributeIsEmptyError`:

.. code-block:: python

    from maxo.errors import AttributeIsEmptyError

    try:
        _ = message.bot
    except AttributeIsEmptyError:
        print("Бот не привязан")

У типов без бота свойства нет: ``user.bot`` упадёт с обычным ``AttributeError``.

Как бот попадает в объект
-------------------------

Обычно привязывать бота вручную не нужно:

- ``Bot.call_method`` привязывает его к ответу API: сообщение из
  ``await bot.send_message(...)`` уже умеет ``edit_message()``;
- ``Dispatcher.feed_update`` привязывает его к апдейту перед хендлерами.

Вручную бота привязывает ``as_(bot)``. Он проставляет бота объекту и всем
вложенным ``FacadeMaxoType`` (например, сообщению внутри апдейта) и
возвращает сам объект:

.. code-block:: python

    update = MessageCreated(message=message, timestamp=now).as_(bot)
    assert update.message.bot is bot

То же для любого объекта, например списка, делает :func:`~maxo.types.bind_bot`.

Бот - поле датакласса, поэтому копии его сохраняют:

.. code-block:: python

    import dataclasses

    copied = dataclasses.replace(update, user_locale="ru")
    assert copied.bot is bot

Реторта поле ``_bot`` не читает и не пишет: в JSON его нет ни при загрузке,
ни при выгрузке. Сравнение ``==`` и ``repr`` его тоже не учитывают.

Собственный тип с ботом
-----------------------

Наследуйте от ``FacadeMaxoType``:

.. code-block:: python

    from maxo.types import FacadeMaxoType

    class UserProfile(FacadeMaxoType):
        user_id: int
        name: str

        async def notify(self, text: str) -> None:
            await self.bot.send_message(user_id=self.user_id, text=text)

    profile = UserProfile(user_id=1, name="Alice").as_(bot)
    await profile.notify("Привет!")

API
---

.. autoclass:: maxo.types.FacadeMaxoType
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. autoclass:: maxo.types.MaxoType
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:
