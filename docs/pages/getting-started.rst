Начало работы
=============

.. meta::
   :description: Установка maxo через uv, poetry или pip и быстрый старт: эхо-бот, обработка команд и клавиатуры. Async-фреймворк для ботов MAX (max.ru) на Python 3.12+.
   :keywords: maxo установка, max.ru бот python, эхо-бот max, быстрый старт maxo, pip install maxo, uv add maxo

Установка
---------

Требования:

- Python: >=3.12,<3.15
- Токен бота, его необходимо получить на `платформе для партнеров <https://business.max.ru/self>`_

.. tab-set::

    .. tab-item:: :iconify:`material-icon-theme:uv` uv

        .. code-block:: bash

            uv add maxo

    .. tab-item:: :iconify:`devicon:poetry` poetry

        .. code-block:: bash

            poetry add maxo

    .. tab-item:: :iconify:`devicon:pypi` pip

        .. code-block:: bash

            pip install maxo

Дополнительные зависимости:

- ``'maxo[dishka]'`` - для поддержки DI через ``dishka``
- ``'maxo[redis]'`` - для использования ``RedisStorage`` в качестве FSM-хранилища
- ``'maxo[magic_filter]'`` - для использования ``MagicFilter`` для условий срабатывания обработчиков

.. note::

  Если вы используете FSM, мы рекомендуем использовать ``redis`` как хранилище состояний в production-среде.


Быстрый старт
-------------

Больше примеров в `examples <https://github.com/K1rL3s/maxo/tree/master/examples>`_ на GitHub.

.. tab-set::

    .. tab-item:: Эхо-бот

       .. code-block:: python
          :linenos:

          import logging
          import os

          from maxo import Bot, Dispatcher
          from maxo.routing.updates import MessageCreated
          from maxo.transport.long_polling import LongPolling

          bot = Bot(os.environ["TOKEN"])
          dispatcher = Dispatcher()

          @dispatcher.message_created()
          async def echo_handler(update: MessageCreated) -> None:
              text = update.message.body.text or "Текста нет"
              await update.answer_text(text)

          logging.basicConfig(level=logging.INFO)
          LongPolling(dispatcher).run(bot)

    .. tab-item:: Команды

       .. code-block:: python
          :linenos:

          import logging
          import os

          from maxo import Bot, Dispatcher, Router
          from maxo.routing.filters import CommandStart
          from maxo.routing.updates import MessageCreated
          from maxo.transport.long_polling import LongPolling

          bot = Bot(os.environ["TOKEN"])
          router = Router()

          @router.message_created(CommandStart())
          # или @router.message_created(Command("start"))
          async def start_handler(update: MessageCreated) -> None:
              await update.answer_text("Привет! Я бот")

          def main():
              logging.basicConfig(level=logging.INFO)
              dispatcher = Dispatcher()
              dispatcher.include(router)
              LongPolling(dispatcher).run(bot)

          if __name__ == "__main__":
              main()

    .. tab-item:: Клавиатура

       .. code-block:: python
          :linenos:

          import logging
          import os

          from magic_filter import F

          from maxo import Bot, Dispatcher, Router
          from maxo.integrations.magic_filter import MagicFilter
          from maxo.routing.filters import CommandStart
          from maxo.routing.updates import MessageCallback, MessageCreated
          from maxo.transport.long_polling import LongPolling
          from maxo.utils.builders import KeyboardBuilder

          bot = Bot(os.environ["TOKEN"])
          router = Router()

          @router.message_created(CommandStart())
          async def start_handler(message: MessageCreated) -> None:
              keyboard = (
                  KeyboardBuilder()
                  .add_callback(
                      text="Нажми меня",
                      payload="my_callback",
                  )
                  .build()
              )
              await message.answer_text(
                  "Это сообщение с клавиатурой:",
                  keyboard=keyboard,
              )

          @router.message_callback(MagicFilter(F.payload == "my_callback"))
          async def button_handler(
              callback: MessageCallback,
              bot: Bot,
          ) -> None:
              await callback.callback_answer("Вы нажали на кнопку!")
              await bot.send_message(
                  user_id=callback.user.user_id,
                  text="Вы нажали на кнопку!",
              )

          def main():
              logging.basicConfig(level=logging.INFO)
              dispatcher = Dispatcher()
              dispatcher.include(router)
              LongPolling(dispatcher).run(bot)

          if __name__ == "__main__":
              main()
