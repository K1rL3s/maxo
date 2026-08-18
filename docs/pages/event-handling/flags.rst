Флаги
=====

.. meta::
   :description: Флаги хендлеров в maxo: установка через декораторы,
      регистрацию и фильтры, чтение из мидлварей и утилит.
   :keywords: maxo флаги, flags maxo, chat_action, rate limit бот max

Флаги хранят метаданные хендлера. Их читают фильтры, мидлвари и утилиты.
Сам хендлер использует флаг, только если прочитает его явно.

Мидлварь может по флагу включить действие «бот набирает сообщение» для долгого
хендлера или ограничить частоту вызовов команды. Фильтр ``Command`` записывает
команды во флаг, из которого можно собрать меню бота.

Как повесить флаг
-----------------

Через декоратор
^^^^^^^^^^^^^^^

Обращение к атрибуту объекта ``flags`` создаёт одноимённый флаг. Декоратор без
аргументов записывает значение ``True``:

.. code-block:: python

    from maxo import flags
    from maxo.types import MessageCreated


    @flags.chat_action
    async def my_handler(update: MessageCreated) -> None: ...

Вызов с одним аргументом задаёт значение флага:

.. code-block:: python

    @flags.chat_action("sending_photo")
    async def my_handler(update: MessageCreated) -> None: ...

Вызов с именованными аргументами кладёт во флаг словарь:

.. code-block:: python

    @flags.rate_limit(rate=2, key="something")
    async def my_handler(update: MessageCreated) -> None: ...

Один хендлер может иметь несколько флагов:

.. code-block:: python

    @dp.message_created(Command("report"))
    @flags.chat_action
    @flags.rate_limit(rate=5)
    async def my_handler(update: MessageCreated) -> None: ...

.. note::

    В примерах проекта декоратор флага стоит **ниже** декоратора регистрации
    хендлера. Поддерживаются оба порядка.

При регистрации хендлера
^^^^^^^^^^^^^^^^^^^^^^^^

Каждый обсёрвер принимает флаги аргументом ``flags``:

.. code-block:: python

    @dp.message_created(Command("report"), flags={"chat_action": "typing_on"})
    async def my_handler(update: MessageCreated) -> None: ...

Флаги можно передать и при явной регистрации:

.. code-block:: python

    dp.message_created.handler(
        my_handler,
        Command("report"),
        flags={"rate_limit": 5},
    )
    dp.message_created.register(
        my_handler,
        Command("report"),
        flags={"rate_limit": 5},
    )

Через фильтры
^^^^^^^^^^^^^

Фильтр на основе ``BaseFilter`` может дополнить флаги хендлера через метод
``update_handler_flags``:

.. code-block:: python

    from typing import Any

    from maxo.routing.filters import BaseFilter
    from maxo.types import MessageCreated


    class Command(BaseFilter[MessageCreated]):
        ...

        def update_handler_flags(self, flags: dict[str, Any]) -> None:
            flags["commands"] = [*flags.get("commands", ()), self]

.. note::

    Словарь флагов копируется поверхностно. Не изменяйте вложенные списки и
    словари на месте - создавайте новое значение. Иначе изменения попадут во
    флаги других хендлеров и в исходный словарь ``flags={...}``.

Встроенный фильтр :class:`~maxo.routing.filters.Command` добавляет себя во флаг
``commands`` через этот метод.

Комбинаторы ``&`` и ``|`` добавляют флаги вложенных фильтров. Например,
``Command("start") | Command("help")`` запишет во флаг ``commands`` обе
команды. Инверсия ``~`` не добавляет флаги вложенного фильтра: хендлер с
``~Command("start")`` обрабатывает всё, кроме ``/start``, поэтому эта команда
не должна попасть в его флаги.

Приоритет
^^^^^^^^^

Если один и тот же флаг задан несколькими способами, побеждает тот, что ближе к
самой функции. Приоритет по убыванию:

1. флаги от декораторов на функции,
2. флаги от фильтров,
3. ``flags={...}`` при регистрации хендлера.

Как прочитать флаг
------------------

Флаги доступны фильтрам хендлера и **inner**-мидлварям. На этом этапе хендлер
уже выбран и хранится в ``ctx`` под ключом ``handler``. В **outer**-мидлварях
и фильтрах обсёрвера (``router.message_created.filter``) хендлер ещё не выбран,
поэтому его флаги недоступны.

.. code-block:: python

    from typing import Any

    from maxo import Ctx
    from maxo.routing.flags import get_flag
    from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
    from maxo.types import MessageCreated


    class RateLimitMiddleware(BaseMiddleware[MessageCreated]):
        async def __call__(
            self,
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            rate_limit = get_flag(ctx, "rate_limit")
            if rate_limit is None:
                return await next(ctx)

            ...
            return await next(ctx)


    dp.message_created.middleware(RateLimitMiddleware())  # именно inner

С дополнительной зависимостью ``maxo[magic_filter]`` флаги можно проверять
через ``magic_filter``:

.. code-block:: python

    from magic_filter import F

    from maxo.integrations.magic_filter import check_flags

    if check_flags(ctx, F.chat_action.action == "sending_photo"):
        ...

Использование в утилитах
------------------------

Флаги хранятся и у зарегистрированных хендлеров, поэтому их можно читать вне
обработки апдейта. Следующая функция обходит дерево роутеров и собирает команды
из флага ``commands``:

.. code-block:: python

    from collections.abc import Iterator

    from maxo import Router
    from maxo.routing.filters import Command


    def collect_commands(router: Router) -> Iterator[str]:
        for handler in router.message_created.handlers:
            for command in handler.flags.get("commands", []):
                yield from (str(name) for name in command.commands)

        for child_router in router.children_routers:
            if isinstance(child_router, Router):
                yield from collect_commands(child_router)

Полученный список можно передать в
``bot.edit_my_commands(commands=...)``.

Флаги в самом maxo
------------------

* ``chat_action`` - :doc:`../utils/chat_action`,
* ``callback_answer`` - :doc:`../utils/callback_answer`,
* ``commands`` - заполняется фильтром :class:`~maxo.routing.filters.Command`.

Справочник
----------

.. automodule:: maxo.routing.flags
   :members: flags, FlagGenerator, FlagDecorator, Flag, extract_flags, extract_flags_from_object, get_flag
   :undoc-members:
   :show-inheritance:

.. autofunction:: maxo.integrations.magic_filter.check_flags
