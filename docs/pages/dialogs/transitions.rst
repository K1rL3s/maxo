=====================
Переходы и навигация
=====================

Ключевая особенность ``maxo.dialogs`` - стек диалогов и маршрутизация между ними.

Управление DialogManager
========================

Для управления диалогами из хэндлеров и кнопок используется ``DialogManager``. Он доступен как аргумент в колбеках или инжектится в обычные хэндлеры через DI.

Основные методы:

- ``start(state, data, mode)`` - открыть новый диалог. Новое состояние добавляется поверх текущего стека диалогов.
- ``switch_to(state)`` - переключить окно в рамках *текущего* диалога.
- ``next()`` / ``back()`` - следующее или предыдущее окно (по порядку их объявления в ``Dialog``).
- ``done(result)`` - закрыть текущий диалог и вернуться к предыдущему (если был запущен поверх). Можно вернуть результат.
- ``update(data)`` - обновить данные текущего контекста и перерисовать сообщение.

Режимы запуска (StartMode)
==========================

При запуске диалога можно указать режим (``mode``):

.. code-block:: python

    from maxo.dialogs import StartMode

NORMAL
------

Режим по умолчанию. Новый диалог помещается **поверх текущего** стека. Текущий диалог «засыпает» и будет продолжен после завершения нового.

.. code-block:: python

    # Открываем новый диалог, не трогая текущий
    await manager.start(ChildSG.main, mode=StartMode.NORMAL)

Используйте, когда нужно «позвать» вложенный диалог (например, форму редактирования) и потом вернуться обратно.

RESET_STACK
-----------

Полностью **очищает стек** диалогов перед запуском нового. Все предыдущие диалоги закрываются.

.. code-block:: python

    # Сбрасываем всё и начинаем с чистого листа
    await manager.start(MainMenuSG.main, mode=StartMode.RESET_STACK)

Используйте для «жёстких» переходов: кнопка «В главное меню», команда ``/start``, или когда нужно гарантировать чистый стек.

NEW_STACK
---------

Создаёт **новый параллельный стек**, не затрагивая старый. Используется редко - для продвинутых сценариев, когда нужно несколько независимых потоков диалогов.

.. code-block:: python

    await manager.start(NotificationSG.main, mode=StartMode.NEW_STACK)

Стек диалогов
=============

Вы можете запускать диалог из другого диалога. При вызове ``start()`` новый диалог оказывается на вершине стека и берет управление на себя. Когда он вызовет ``done(result)``, он закроется, и управление вернется к предыдущему диалогу, который получит этот ``result`` через обработчик ``on_process_result`` (определяемый в ``Dialog()``).

Пример: основной диалог и вложенный
------------------------------------

.. code-block:: python

    from maxo.dialogs import Dialog, DialogManager, StartMode, Window
    from maxo.dialogs.widgets.kbd import Button
    from maxo.dialogs.widgets.text import Const, Format
    from maxo.fsm import State, StatesGroup
    from maxo.routing.updates import MessageCallback

    # --- Вложенный диалог: выбор цвета ---

    class ColorSG(StatesGroup):
        pick = State()

    async def on_red(callback: MessageCallback, button: Button, manager: DialogManager):
        await manager.done(result="red")

    async def on_blue(callback: MessageCallback, button: Button, manager: DialogManager):
        await manager.done(result="blue")

    color_dialog = Dialog(
        Window(
            Const("Выберите цвет:"),
            Button(Const("🔴 Красный"), id="red", on_click=on_red),
            Button(Const("🔵 Синий"), id="blue", on_click=on_blue),
            state=ColorSG.pick,
        ),
    )

    # --- Основной диалог ---

    class MainSG(StatesGroup):
        menu = State()

    async def on_pick_color(callback: MessageCallback, button: Button, manager: DialogManager):
        # Запускаем вложенный диалог
        await manager.start(ColorSG.pick, mode=StartMode.NORMAL)

    async def on_color_chosen(start_data, result, manager: DialogManager):
        """Вызывается, когда вложенный диалог завершился через done()."""
        if result:
            manager.dialog_data["color"] = result

    async def main_getter(dialog_manager: DialogManager, **kwargs):
        color = dialog_manager.dialog_data.get("color", "не выбран")
        return {"color": color}

    main_dialog = Dialog(
        Window(
            Format("Текущий цвет: {color}"),
            Button(Const("Выбрать цвет"), id="pick", on_click=on_pick_color),
            state=MainSG.menu,
            getter=main_getter,
        ),
        on_process_result=on_color_chosen,
    )
