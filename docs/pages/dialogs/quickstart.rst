=============
Быстрый старт
=============

.. meta::
   :description: Быстрый старт с maxo.dialogs - диалоги для ботов MAX (max.ru): создание окон, виджетов, состояний и переходов на основе aiogram_dialog.
   :keywords: maxo dialogs, диалоги бот max, aiogram_dialog max.ru, окна и состояния, виджеты бот, FSM диалоги

Чтобы начать использовать ``maxo.dialogs``, давайте создадим простое эхо-меню с кнопкой.

Подготовка состояний
====================

Каждое окно в диалоге привязывается к состоянию из ``StatesGroup``.

.. code-block:: python

    from maxo.fsm import State, StatesGroup

    class MyDialog(StatesGroup):
        main = State()

Создание окна и диалога
=======================

Окно содержит элементы UI (виджеты). Соберем диалог из одного окна:

.. code-block:: python

    from maxo.dialogs import Dialog, DialogManager, Window
    from maxo.dialogs.widgets.kbd import Button
    from maxo.dialogs.widgets.text import Const
    from maxo.routing.updates import MessageCallback

    async def on_click(callback: MessageCallback, button: Button, manager: DialogManager):
        await manager.answer_callback()

    dialog = Dialog(
        Window(
            Const("Привет! Это твой первый диалог на maxo.dialogs."),
            Button(Const("Нажми меня"), id="btn1", on_click=on_click),
            state=MyDialog.main,
        ),
    )


Точка входа
===========

Теперь нам нужен хэндлер (например, на команду ``/start``), который запустит диалог. Чтобы запустить диалог, используйте метод ``start()`` у ``DialogManager``:

.. code-block:: python

    from maxo import Router
    from maxo.dialogs import DialogManager, StartMode
    from maxo.routing.filters import Command
    from maxo.routing.updates import MessageCreated

    router = Router()

    @router.message_created(Command("start"))
    async def start_handler(message: MessageCreated, dialog_manager: DialogManager):
        await dialog_manager.start(MyDialog.main, mode=StartMode.RESET_STACK)

Регистрация в приложении
========================

Осталось только собрать всё вместе и зарегистрировать систему диалогов в корневом роутере. Вызовите ``setup_dialogs(dp)``.

.. code-block:: python

    from maxo import Bot, Dispatcher, Router
    from maxo.dialogs import setup_dialogs
    from maxo.fsm.key_builder import DefaultKeyBuilder
    from maxo.transport.long_polling import LongPolling

    def main():
        key_builder = DefaultKeyBuilder(with_destiny=True)

        bot = Bot("ВАШ ТОКЕН БОТА")
        dp = Dispatcher(key_builder=key_builder)

        # Подключаем роутер с хэндлером и роутер (диалог)
        dp.include(router)
        dp.include(dialog)

        # Важно! Инициализируем систему диалогов
        setup_dialogs(dp)

        LongPolling(dp).run(bot)

    if __name__ == "__main__":
        main()


.. note::

   При использовании ``setup_dialogs`` с FSM-хранилищем необходимо всегда передавать ``KeyBuilder`` с ``with_destiny=True``:

   .. code-block:: python

       from maxo.fsm.key_builder import DefaultKeyBuilder

       key_builder = DefaultKeyBuilder(with_destiny=True)
       dp = Dispatcher(key_builder=key_builder)

   Подробнее: `issue #34 <https://github.com/K1rL3s/maxo/issues/34>`_.
