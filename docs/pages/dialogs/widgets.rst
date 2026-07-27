========
Виджеты
========

Виджеты - компоненты, из которых строится содержимое окна (``Window``). Все виджеты делятся на текстовые, клавиатурные, медиа-виджеты и поля ввода.

.. note::

    В обработчиках ``on_click`` ``callback.message`` может быть ``None``, если
    исходное сообщение удалили до того, как бот получил колбэк - тогда
    ``unsafe_message`` бросит ``AttributeIsEmptyError``.
    Подробнее в :ref:`разделе про unsafe_* <message-callback-none>`.

Текстовые виджеты
=================

Отвечают за текстовое содержимое сообщения.

Const
-----

Статический текст, который не зависит от данных.

.. code-block:: python

    from maxo.dialogs.widgets.text import Const

    Const("Добро пожаловать в бота!")

Format
------

Динамический текст с форматированием через ``.format()``. Ключи подставляются из словаря, возвращённого геттером.

.. code-block:: python

    from maxo.dialogs.widgets.text import Format

    # В геттере: return {"name": "Иван", "balance": 100}
    Format("Привет, {name}! Твой баланс: {balance} ₽")

Jinja
-----

Шаблоны Jinja2. Подходят для сложной логики рендеринга с условиями и циклами.

.. code-block:: python

    from maxo.dialogs.widgets.text import Jinja

    Jinja("""
    Привет, {{ user.name }}!
    {% if user.is_admin %}🔑 Вы администратор{% endif %}
    """)

Multi и Case
------------

``Multi`` отображает несколько текстовых виджетов друг за другом.
``Case`` выбирает один из вариантов в зависимости от значения ключа из данных.

.. code-block:: python

    from maxo.dialogs.widgets.text import Case, Const, Format, Multi

    Multi(
        Const("Добро пожаловать!"),
        Format("Текущий язык: {lang}"),
    )

    # selector - ключ из данных геттера, texts - варианты
    Case(
        texts={
            "en": Const("Hello!"),
            "ru": Const("Привет!"),
        },
        selector="lang",
    )

Клавиатурные виджеты
====================

Используются для создания Inline-кнопок.

Button
------

Простая кнопка с обработчиком нажатия.

.. code-block:: python

    from maxo.dialogs.api.protocols import DialogManager
    from maxo.dialogs.widgets.kbd import Button
    from maxo.dialogs.widgets.text import Const
    from maxo.types import MessageCallback

    async def on_click(callback: MessageCallback, button: Button, manager: DialogManager):
        await callback.callback_answer("Вы нажали на кнопку!")

    Button(Const("Нажми меня"), id="btn1", on_click=on_click)

Url
---

Кнопка-ссылка. При нажатии открывает URL.

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Url
    from maxo.dialogs.widgets.text import Const

    Url(Const("Открыть сайт"), Const("https://example.com"))

Clipboard
---------

Кнопка, при нажатии на которую в буфер обмена пользователя копируется переданный текст.

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Clipboard
    from maxo.dialogs.widgets.text import Const

    Clipboard(Const("Скопировать"), Const("Текст для копирования"))

Row, Column, Group
------------------

Группировка кнопок в строку, столбец или произвольную группу.

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Button, Column, Group, Row
    from maxo.dialogs.widgets.text import Const

    # Две кнопки в одной строке
    Row(
        Button(Const("Да"), id="yes", on_click=on_click),
        Button(Const("Нет"), id="no", on_click=on_click),
    )

    # Три кнопки в столбец (каждая в своей строке)
    Column(
        Button(Const("Первый"), id="b1", on_click=on_click),
        Button(Const("Второй"), id="b2", on_click=on_click),
        Button(Const("Третий"), id="b3", on_click=on_click),
    )

    # Group с фиксированной шириной (2 кнопки в строке)
    Group(
        Button(Const("A"), id="a", on_click=on_click),
        Button(Const("B"), id="b", on_click=on_click),
        Button(Const("C"), id="c", on_click=on_click),
        Button(Const("D"), id="d", on_click=on_click),
        width=2,
    )

Select
------

Список выбора: динамически генерирует кнопки из данных.

.. code-block:: python

    from maxo.dialogs.api.protocols import DialogManager
    from maxo.dialogs.widgets.kbd import Select
    from maxo.dialogs.widgets.text import Format
    from maxo.types import MessageCallback

    async def on_fruit_selected(callback: MessageCallback, widget: Select, manager: DialogManager, item_id: str):
        await callback.callback_answer(f"Вы выбрали: {item_id}")

    # items - ключ из данных геттера (list[tuple[str, str]])
    # В геттере: return {"fruits": [("apple", "🍎 Яблоко"), ("banana", "🍌 Банан")]}
    Select(
        Format("{item[1]}"),  # текст кнопки
        id="fruit_select",
        item_id_getter=lambda item: item[0],  # ID элемента
        items="fruits",  # ключ из данных
        on_click=on_fruit_selected,
    )

Radio
-----

Переключатель - позволяет выбрать один элемент из списка. Выбранный элемент отмечается.

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Radio
    from maxo.dialogs.widgets.text import Format

    Radio(
        Format("✅ {item[1]}"),  # текст для выбранного
        Format("  {item[1]}"),  # текст для невыбранного
        id="lang_radio",
        item_id_getter=lambda item: item[0],
        items="languages",
        # В геттере: return {"languages": [("ru", "Русский"), ("en", "English")]}
    )

ConfirmButton
-------------

Кнопка с двойным подтверждением. При первом нажатии переходит в состояние ожидания - показывает опциональный предупреждающий текст и кнопки «Отмена» / «Подтвердить». При повторном нажатии вызывает соответствующий обработчик.

**Ключевая особенность:** виджет не хранит состояние в данных диалога - оно выводится из payload кнопки. Благодаря этому при переходе в другое окно и обратно кнопка автоматически сбрасывается в исходное (primary) состояние.

Использование
^^^^^^^^^^^^^

.. code-block:: python

    from maxo.dialogs.api.protocols import DialogManager
    from maxo.dialogs.widgets.kbd import ConfirmButton
    from maxo.dialogs.widgets.text import Const
    from maxo.types import MessageCallback

    async def on_confirm(
        callback: MessageCallback,
        widget: ConfirmButton,
        manager: DialogManager,
    ) -> None:
        await callback.unsafe_message.answer("Действие подтверждено!")

    async def on_cancel(
        callback: MessageCallback,
        widget: ConfirmButton,
        manager: DialogManager,
    ) -> None:
        await callback.unsafe_message.answer("Действие отменено.")

    # Режим с предупредительным текстом (2 шага):
    # primary → warning + [Отмена] [Подтвердить] → on_confirm / on_cancel
    ConfirmButton(
        id="delete_btn",
        primary_text=Const("🗑 Удалить"),
        confirm_text=Const("✅ Да, удалить"),
        cancel_text=Const("❌ Отмена"),
        warning_text=Const("⚠️ Вы уверены?"),
        on_confirm=on_confirm,
        on_cancel=on_cancel,
    )

    # Режим без предупредительного текста (1 шаг):
    # primary → [Отмена] [Подтвердить] (без строки с текстом)
    ConfirmButton(
        id="buy_btn",
        primary_text=Const("🛒 Купить"),
        confirm_text=Const("✅ Купить"),
        cancel_text=Const("❌ Нет"),
        warning_text=None,  # строка-предупреждение не отображается
        on_confirm=on_confirm,
        on_cancel=None,    # при отмене просто возвращается primary
    )

Параметры
^^^^^^^^^

*   **id** (:py:class:`str`): Уникальный идентификатор виджета. Используется для различения нескольких ``ConfirmButton`` в одном окне.
*   **primary_text** (:py:class:`~maxo.dialogs.api.internal.TextWidget`): Текст кнопки в исходном состоянии.
*   **confirm_text** (:py:class:`~maxo.dialogs.api.internal.TextWidget`): Текст кнопки подтверждения в состоянии ожидания.
*   **cancel_text** (:py:class:`~maxo.dialogs.api.internal.TextWidget`): Текст кнопки отмены в состоянии ожидания.
*   **warning_text** (:py:class:`~maxo.dialogs.api.internal.TextWidget` | ``None``, optional): Текст предупреждения, отображаемый отдельной строкой над кнопками отмены/подтверждения. Если ``None`` - строка не добавляется, кнопки появляются сразу. По умолчанию ``None``.
*   **on_confirm** (:py:class:`~maxo.dialogs.widgets.kbd.confirm_button.OnClick` | ``None``, optional): Обработчик, вызываемый при нажатии кнопки подтверждения. По умолчанию ``None`` (no-op).
*   **on_cancel** (:py:class:`~maxo.dialogs.widgets.kbd.confirm_button.OnClick` | ``None``, optional): Обработчик, вызываемый при нажатии кнопки отмены. По умолчанию ``None`` (no-op, виджет возвращается в primary).
*   **confirm_first** (:py:class:`bool`, optional): Если ``True`` - кнопка подтверждения отображается левее кнопки отмены. По умолчанию ``False`` (порядок: «Отмена» | «Подтвердить»).
*   **oneline** (:py:class:`bool`, optional): Если ``True`` - кнопки отмены и подтверждения будут в одном ряду, иначе в двух. По умолчанию ``True``
*   **when** (:py:class:`~maxo.dialogs.widgets.common.WhenCondition`, optional): Условие, при котором виджет отображается. При ``False`` виджет полностью скрывается.

Поведение при переходах между окнами
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``ConfirmButton`` намеренно не сохраняет состояние ожидания в данных диалога. Это означает, что при переходе в другое окно (``SwitchTo``, ``Next``, ``Back``) и возврате обратно кнопка всегда отрисовывается в исходном (primary) состоянии. Такое поведение позволяет избежать «зависшего» состояния подтверждения при навигации.

.. code-block:: python

    from maxo.dialogs.widgets.kbd import ConfirmButton, SwitchTo
    from maxo.dialogs.widgets.text import Const

    # В этом примере при возврате из SG.settings обратно в SG.main
    # кнопка delete_btn будет снова показана как "🗑 Удалить", а не как
    # "⚠️ Вы уверены? / [Отмена] [Да, удалить]"
    Window(
        Const("Главное меню"),
        ConfirmButton(
            id="delete_btn",
            primary_text=Const("🗑 Удалить"),
            confirm_text=Const("✅ Да, удалить"),
            cancel_text=Const("❌ Отмена"),
            warning_text=Const("⚠️ Вы уверены?"),
            on_confirm=on_confirm,
        ),
        SwitchTo(Const("⚙️ Настройки"), id="to_settings", state=SG.settings),
        state=SG.main,
    )

Несколько кнопок в одном окне
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

В одном окне можно разместить несколько ``ConfirmButton`` - они не пересекаются по payload-префиксу, поскольку каждый виджет использует свой уникальный ``id``.

.. code-block:: python

    Window(
        Const("Выберите заказ:"),
        ConfirmButton(
            id="pizza",
            primary_text=Const("🍕 Заказать пиццу"),
            confirm_text=Const("✅ Точно"),
            cancel_text=Const("❌ Передумал"),
            warning_text=Const("🍕 Подтверди заказ пиццы"),
            on_confirm=on_pizza,
            on_cancel=on_pizza_cancel,
        ),
        ConfirmButton(
            id="sushi",
            primary_text=Const("🍣 Заказать суши"),
            confirm_text=Const("✅ Точно суши"),
            cancel_text=Const("❌ Передумал, не суши"),
            on_confirm=on_sushi,
        ),
        state=SG.main,
    )

TimeSelect
----------

Виджет для выбора времени (часы и минуты). Представляет собой две отдельные клавиатуры для выбора часов и минут, что позволяет пользователю легко ввести нужное время.

Использование
^^^^^^^^^^^^^

.. code-block:: python

    from datetime import time

    from maxo.dialogs import Dialog, DialogManager, Window
    from maxo.dialogs.widgets.kbd import TimeSelect
    from maxo.dialogs.widgets.text import Const
    from maxo.fsm import State, StatesGroup


    class MySG(StatesGroup):
        time_selection = State()

    async def on_time_selected(event, widget, manager: DialogManager, selected_time: time):
        # Здесь можно обработать выбранное время
        await event.callback_answer(f"Вы выбрали время: {selected_time.strftime('%H:%M')}")
        manager.dialog_data["selected_time"] = selected_time

    dialog = Dialog(
        Window(
            Const("Выберите время:"),
            TimeSelect(
                id="time_selector",
                on_value_changed=on_time_selected,
            ),
            state=MySG.time_selection,
        )
    )

Параметры
^^^^^^^^^

*   **id** (:py:class:`str`): Уникальный идентификатор виджета.
*   **when** (:py:class:`~maxo.dialogs.widgets.common.WhenCondition`, optional): Условие, при котором виджет будет отображаться.
*   **hour_header** (:py:class:`~maxo.dialogs.widgets.text.TextWidget`, optional): Текст заголовка для выбора часов. По умолчанию "Hour".
*   **minute_header** (:py:class:`~maxo.dialogs.widgets.text.TextWidget`, optional): Текст заголовка для выбора минут. По умолчанию "Minute".
*   **button_text** (:py:class:`~maxo.dialogs.widgets.text.TextWidget`, optional): Формат текста для кнопок часов/минут, которые не выбраны. По умолчанию "{value}".
*   **button_selected_text** (:py:class:`~maxo.dialogs.widgets.text.TextWidget`, optional): Формат текста для выбранных кнопок часов/минут. По умолчанию "[{value}]".
*   **on_hour_click** (:py:class:`~maxo.dialogs.widgets.kbd.time.OnClick`, optional): Обработчик нажатия на кнопку часа.
*   **on_minute_click** (:py:class:`~maxo.dialogs.widgets.kbd.time.OnClick`, optional): Обработчик нажатия на кнопку минуты.
*   **on_value_changed** (:py:class:`~maxo.dialogs.widgets.kbd.time.OnValueChanged`, optional): Обработчик изменения выбранного времени. Принимает аргументы ``event``, ``widget``, ``manager``, ``value: datetime.time``.
*   **hour_width** (:py:class:`int`, optional): Количество кнопок часов в одной строке. По умолчанию 6.
*   **minute_precision** (:py:class:`int`, optional): Шаг для минут (например, 5 для 0, 5, 10... минут). По умолчанию 5.
*   **minute_width** (:py:class:`int`, optional): Количество кнопок минут в одной строке. По умолчанию 6.

Управление виджетом (ManagedTimeSelect)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Вы можете получить или установить выбранное время программно с помощью ``ManagedTimeSelect``, который доступен через ``widget`` в обработчиках, или через ``manager.find(widget_id).get_value()``.

*   **get_value() -> datetime.time | None**: Возвращает выбранное время или ``None``, если ничего не выбрано.
*   **set_value(value: datetime.time | None)**: Устанавливает выбранное время.

Навигационные кнопки
--------------------

Готовые кнопки для переключения между окнами без написания обработчиков:

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Next, Back, SwitchTo
    from maxo.dialogs.widgets.text import Const

    # Следующее окно (по порядку объявления в Dialog)
    Next(Const("Далее →"), id="next")

    # Предыдущее окно
    Back(Const("← Назад"), id="back")

    # Переключиться на конкретное состояние
    SwitchTo(Const("В настройки"), id="to_settings", state=SG.settings)

Прочие виджеты
==============

DynamicMedia / StaticMedia
--------------------------

Окно может содержать медиа (фото, видео, документ). Вы можете возвращать URL или ID файла.

.. code-block:: python

    from maxo.dialogs.widgets.media import DynamicMedia

    async def media_getter(dialog_manager, **kwargs):
        return {"photo_url": "https://example.com/photo.jpg"}

    # Предполагается использование в Window с getter=media_getter

MessageInput
------------

Слушает текстовые сообщения от пользователя, находясь в конкретном окне. Используется для сбора свободного текстового ввода.

.. code-block:: python

    from maxo.dialogs.widgets.input import MessageInput

    async def on_message(message, widget, manager):
        manager.dialog_data["user_input"] = message.text
        await manager.next()

    Window(
        Const("Введите ваше имя:"),
        MessageInput(on_message),
        state=SG.input_name,
    )
