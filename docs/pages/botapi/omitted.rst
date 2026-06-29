Omitted
=======

При работе с API часто нужно отличить два случая:

- **Параметр не передан** - сервер оставляет текущее значение без изменений.
- **Параметр равен** ``None`` - сервер обнуляет (удаляет) значение.

В Python оба случая обычно выражаются через ``None``, что создаёт неоднозначность.
**maxo** решает эту проблему с помощью sentinel-объекта ``Omitted``.


Проблема
--------

Рассмотрим метод редактирования сообщения:

.. code-block:: python

    from maxo.bot.methods.messages.edit_message import EditMessage

    # Отправляем запрос БЕЗ поля attachments в JSON -
    # сервер не трогает текущие вложения.
    edit = EditMessage(message_id="123", text="Новый текст")

    # Отправляем запрос с attachments=None -
    # сервер УДАЛЯЕТ все вложения.
    edit = EditMessage(message_id="123", text="Новый текст", attachments=None)

Если бы ``attachments`` по умолчанию был ``None``, фреймворк не смог бы отличить
«пользователь явно передал None» от «пользователь ничего не указал».
Именно для этого существует ``Omitted``.


Как это работает
----------------

Поля с типом ``Omittable[T]`` по умолчанию имеют значение ``Omitted()``.
При сериализации запроса такие поля **полностью исключаются** из JSON body и query-параметров.

.. code-block:: python

    from maxo.bot.methods.messages.send_message import SendMessage

    msg = SendMessage(text="Привет!")
    # chat_id, user_id, notify, format - всё Omitted().
    # В запрос попадёт только {"text": "Привет!"}

    msg = SendMessage(text="Привет!", chat_id=123, notify=False)
    # В запрос попадёт:
    #   query: ?chat_id=123
    #   body:  {"text": "Привет!", "notify": false}

Если значение ``Omitted()`` - поле не отправляется.
Если значение ``None`` - поле отправляется как ``null``.
Если значение задано - поле отправляется как есть.


Модуль ``maxo.omit``
---------------------

.. code-block:: python

    from maxo.omit import (
        Omitted,
        Omittable,
        is_omitted,
        is_not_omitted,
        is_defined,
        is_not_defined,
    )


``Omitted``
~~~~~~~~~~~

Класс-sentinel. Экземпляр ``Omitted()`` означает «значение не задано».

.. code-block:: python

    from maxo.omit import Omitted

    value = Omitted()


``Omittable[T]``
~~~~~~~~~~~~~~~~

Type alias: ``T | Omitted``. Используется в аннотациях типов для обозначения
необязательных параметров.

.. code-block:: python

    from maxo.omit import Omittable, Omitted

    def greet(name: Omittable[str] = Omitted()) -> str:
        ...


Guard-функции
~~~~~~~~~~~~~

Четыре функции с поддержкой ``TypeIs`` (сужение типов):

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Функция
     - Описание
   * - ``is_omitted(value)``
     - ``True``, если значение - ``Omitted``
   * - ``is_not_omitted(value)``
     - ``True``, если значение - **не** ``Omitted`` (может быть ``None``)
   * - ``is_defined(value)``
     - ``True``, если значение - **не** ``Omitted`` **и не** ``None``
   * - ``is_not_defined(value)``
     - ``True``, если значение - ``Omitted`` **или** ``None``

.. code-block:: python

    from maxo.omit import Omitted, is_defined, is_omitted

    value: int | None | Omitted = get_value()

    if is_omitted(value):
        print("Не передано")
    elif value is None:
        print("Передано None")
    else:
        print(f"Значение: {value}")

    # is_defined - удобная проверка «есть реальное значение»
    if is_defined(value):
        print(f"Точно число: {value + 1}")  # mypy знает, что value: int


Omitted в объектах ответа
-------------------------

``Omitted`` используется не только при отправке запросов, но и в объектах,
которые приходят **от** API. MAX.ru может не включать некоторые поля в ответ -
например, ``sender`` у сообщения в канале или ``pinned_message`` у чата,
если закреплённого сообщения нет.

В таких случаях поле будет содержать ``Omitted()``, а не ``None``.
Это важное отличие: ``None`` означает, что API явно вернул ``null``,
а ``Omitted()`` - что поле **отсутствовало** в JSON.

.. code-block:: python

    from maxo.routing.updates.message_created import MessageCreated
    from maxo.omit import is_defined, is_omitted

    @dispatcher.message_created()
    async def handler(update: MessageCreated) -> None:
        msg = update.message

        # sender может отсутствовать (например, системное сообщение)
        if is_defined(msg.sender):
            print(f"Отправитель: {msg.sender.first_name}")
        elif is_omitted(msg.sender):
            print("Отправитель неизвестен (поле отсутствует)")

        # url есть только у постов в каналах
        if is_defined(msg.url):
            print(f"Ссылка на пост: {msg.url}")

Паттерн ``unsafe_*``
~~~~~~~~~~~~~~~~~~~~~

Для удобства многие типы предоставляют свойства ``unsafe_*``,
которые возвращают значение напрямую или бросают ``AttributeIsEmptyError``,
если поле содержит ``Omitted()`` или ``None``:

.. code-block:: python

    from maxo.routing.updates.message_created import MessageCreated
    from maxo.omit import is_defined
    from maxo.errors import AttributeIsEmptyError

    @dispatcher.message_created()
    async def handler(update: MessageCreated) -> None:
        # Безопасный доступ - проверяйте сами:
        if is_defined(update.message.sender):
            name = update.message.sender.first_name

        # Или используйте unsafe_ - короче, но бросит исключение,
        # если поля нет:
        try:
            name = update.message.unsafe_sender.first_name
        except AttributeIsEmptyError:
            name = "Аноним"

Типы с ``Omittable``-полями в ответах: ``Message`` (``sender``, ``link``, ``stat``, ``url``),
``Chat`` (``pinned_message``, ``owner_id``, ``link``, ``dialog_with_user``),
``User`` (``last_name``, ``name``), ``VideoAttachment`` (``duration``, ``width``, ``height``)
и многие другие.


Примеры
-------

Использование в фасадах
~~~~~~~~~~~~~~~~~~~~~~~~

Фасады оборачивают методы API и прокидывают ``Omittable``-параметры:

.. code-block:: python

    from maxo.routing.updates import MessageCreated

    @dispatcher.message_created()
    async def handler(message: MessageCreated) -> None:
        # notify не указан -> Omitted -> не попадёт в запрос -> сервер использует значение по умолчанию (true)
        await message.answer_text("Привет!")

        # notify=False -> попадёт в запрос -> участники чата НЕ получат уведомление
        await message.answer_text("Тихое сообщение", notify=False)


Проверка в своём коде
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from maxo.omit import Omittable, Omitted, is_defined

    def build_greeting(
        name: Omittable[str] = Omitted(),
        greeting: Omittable[str] = Omitted(),
    ) -> str:
        parts = []
        if is_defined(greeting):
            parts.append(greeting)
        else:
            parts.append("Привет")
        if is_defined(name):
            parts.append(name)
        return ", ".join(parts) + "!"

    build_greeting()                          # "Привет!"
    build_greeting(name="Кирилл")            # "Привет, Кирилл!"
    build_greeting(greeting="Здравствуйте")  # "Здравствуйте!"


Шпаргалка
----------

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Значение
     - ``is_omitted``
     - ``is_defined``
     - Поведение при отправке запроса
   * - ``Omitted()``
     - ``True``
     - ``False``
     - Поле **не включается** в запрос
   * - ``None``
     - ``False``
     - ``False``
     - Поле отправляется как ``null``
   * - ``"hello"``
     - ``False``
     - ``True``
     - Поле отправляется со значением
