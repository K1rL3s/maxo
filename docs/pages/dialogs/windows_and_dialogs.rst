================
Окна и диалоги
================

В ``maxo.dialogs`` интерфейс пользователя строится из окон (``Window``), которые объединяются в диалоги (``Dialog``).

Window
======

``Window`` - базовый кирпичик интерфейса. Каждое окно соответствует одному сообщению бота с клавиатурой. Окно привязывается к конкретному состоянию конечного автомата (``State``).

Создание окна:

.. code-block:: python

    from maxo.dialogs import Window
    from maxo.dialogs.widgets.text import Const
    from maxo.fsm import State, StatesGroup

    class MySG(StatesGroup):
        first = State()

    window = Window(
        Const("Текст окна"),
        state=MySG.first,
        # Опционально: disable_web_page_preview, parse_mode
    )

Dialog
======

``Dialog`` - это набор окон, связанных логикой переходов. Диалог управляет жизненным циклом окон и хранит их общее состояние.

.. code-block:: python

    from maxo.dialogs import Dialog

    dialog = Dialog(
        window1,
        window2,
        window3,
        # другие окна...
    )

.. important::

   Все окна внутри одного диалога **должны** принадлежать одному ``StatesGroup``.

Жизненный цикл диалога
======================

Диалог можно рассматривать как функцию, которая:

1. Запускается (вызов через ``DialogManager.start()``)
2. Получает данные (аргумент ``start_data``)
3. Меняет внутренние состояния (переключение между окнами)
4. Завершается (возврат через ``DialogManager.done()``)
5. Может возвращать результат (параметр ``result``)

Вы можете перехватывать эти события с помощью параметров ``on_start``, ``on_close``, ``on_process_result`` при создании ``Dialog``:

.. code-block:: python

    from maxo.dialogs import Dialog, DialogManager

    async def on_dialog_start(start_data: dict, manager: DialogManager):
        print("Dialog started with data:", start_data)

    dialog = Dialog(
        window,
        on_start=on_dialog_start,
    )
