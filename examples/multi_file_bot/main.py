"""
Бот, разнесённый по файлам: точка входа main.py и роутеры в handlers/.
Запуск из корня репозитория: python examples/multi_file_bot/main.py
или из этой папки: python main.py
"""

import logging
import os

from handlers import echo_router, start_router

from maxo import Bot, Dispatcher


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    token = os.environ.get("TOKEN") or os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("Задайте TOKEN или BOT_TOKEN в окружении")

    bot = Bot(token)
    dp = Dispatcher()
    dp.include(start_router, echo_router)
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
