=================
Данные и контекст
=================

Данные, необходимые для рендеринга текста, клавиатур и медиа в окне, берутся из словаря (контекста).

Геттеры (Getters)
=================

Геттер - это функция, возвращающая словарь с данными для шаблонов и форматов. Геттер можно повесить как на всё окно (``Window``), так и на весь диалог (``Dialog``). Словари объединяются.

Геттер на окно
--------------

.. code-block:: python

    from maxo.dialogs import Window
    from maxo.dialogs.widgets.text import Format
    from maxo.fsm import State, StatesGroup

    class SG(StatesGroup):
        main = State()

    async def get_user_data(**kwargs):
        return {"name": "Иван", "balance": 100}

    Window(
        Format("Пользователь {name}, баланс: {balance}"),
        state=SG.main,
        getter=get_user_data,
    )

Геттер на диалог
----------------

Если один и тот же набор данных нужен во всех окнах диалога, удобнее повесить геттер на весь ``Dialog``. Он будет вызван для каждого окна, а его результат объединится со словарём локального геттера окна.

.. code-block:: python

    from maxo.dialogs import Dialog, Window
    from maxo.dialogs.widgets.text import Const, Format
    from maxo.fsm import State, StatesGroup

    class SG(StatesGroup):
        main = State()
        details = State()

    async def common_getter(**kwargs):
        """Общий геттер - данные доступны во всех окнах."""
        return {"app_name": "МойБот", "version": "1.0"}

    async def details_getter(**kwargs):
        """Локальный геттер - только для окна details."""
        return {"info": "Подробная информация"}

    dialog = Dialog(
        Window(
            Format("{app_name} v{version}"),
            Const("Главное окно"),
            state=SG.main,
        ),
        Window(
            Format("{app_name}: {info}"),
            state=SG.details,
            getter=details_getter,  # локальный геттер
        ),
        getter=common_getter,  # общий геттер для всех окон
    )

Данные из Middleware
====================

Геттеры поддерживают Dependency Injection (как и обычные хэндлеры ``maxo``). Данные из мидлварей автоматически доступны в геттерах.

Например, если у вас есть мидлварь, которая по каждому событию достаёт из базы объект текущего пользователя:

.. code-block:: python

    from typing import Any

    from maxo.routing.ctx import Ctx
    from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
    from maxo.routing.updates import MessageCreated

    class UserMiddleware(BaseMiddleware[MessageCreated]):
        async def __call__(
            self,
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            user = await get_user_from_db(update.message.unsafe_sender.user_id)
            ctx["user"] = user  # кладём в контекст
            return await next(ctx)

То в геттере вы можете принять ``user`` через аргумент:

.. code-block:: python

    async def get_user_data(user: User, **kwargs):
        # user подставляется из мидлвари автоматически
        return {"name": user.full_name, "balance": user.balance}

.. seealso::

   Подробнее о создании и регистрации мидлварей: :doc:`/pages/event-handling/middlewares`.

DialogData и StartData
======================

Помимо геттеров, у ``DialogManager`` есть доступ к состоянию диалога через два ключевых словаря.

start_data - данные между диалогами
------------------------------------

``start_data`` - это **неизменяемые** данные, переданные при запуске диалога через ``manager.start(state, data={...})``. Используются для передачи начальных параметров **из одного диалога в другой** (или из хэндлера в диалог).

**Пример 1: Запуск диалога из хэндлера с данными**

.. code-block:: python

    from maxo.dialogs import DialogManager
    from maxo.routing.filters import Command
    from maxo.routing.updates import MessageCreated

    @router.message_created(Command("profile"))
    async def show_profile(message: MessageCreated, dialog_manager: DialogManager):
        await dialog_manager.start(
            ProfileSG.main,
            data={"user_id": message.message.sender.user_id},
        )

**Пример 2: Чтение start_data в геттере**

.. code-block:: python

    from maxo.dialogs import DialogManager

    async def profile_getter(dialog_manager: DialogManager, **kwargs):
        user_id = dialog_manager.start_data["user_id"]
        user = await get_user_from_db(user_id)
        return {"name": user.name, "age": user.age}

**Пример 3: Запуск вложенного диалога с данными**

.. code-block:: python

    from maxo.dialogs import DialogManager
    from maxo.dialogs.widgets.kbd import Button
    from maxo.routing.updates import MessageCallback

    async def on_edit_click(
        callback: MessageCallback,
        button: Button,
        dialog_manager: DialogManager,
    ) -> None:
        # Передаём данные из текущего диалога в дочерний
        await dialog_manager.start(
            EditSG.main,
            data={"item_id": dialog_manager.dialog_data["selected_item"]},
        )


dialog_data - данные между окнами
----------------------------------

``dialog_data`` - это **мутируемый** словарь для хранения промежуточных данных **внутри одного диалога**, между переходами окон. Аналог FSM-хранилища, но привязан к конкретному диалогу.

.. code-block:: python

    from maxo.dialogs import DialogManager
    from maxo.dialogs.widgets.input import MessageInput
    from maxo.routing.updates import MessageCreated

    async def on_name_input(message: MessageCreated, widget: MessageInput, manager: DialogManager):
        manager.dialog_data["name"] = message.message.body.text
        await manager.next()

    async def on_age_input(message: MessageCreated, widget: MessageInput, manager: DialogManager):
        manager.dialog_data["age"] = message.message.body.text
        await manager.next()

    async def summary_getter(dialog_manager: DialogManager, **kwargs):
        return {
            "name": dialog_manager.dialog_data.get("name", "-"),
            "age": dialog_manager.dialog_data.get("age", "-"),
        }

.. important::

   **Главное отличие:**

   - ``start_data`` - передаётся извне при запуске и **не изменяется**. Для связи *между* диалогами.
   - ``dialog_data`` - создаётся внутри диалога и **свободно мутируется**. Для связи *между окнами* одного диалога.
