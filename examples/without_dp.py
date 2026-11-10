import asyncio
import logging
import os

from maxo import Bot


# Отправка сообщения без Dispatcher - только Bot и API
async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    token = os.environ["TOKEN"]
    chat_id = os.environ.get("CHAT_ID")
    message = os.environ.get("MESSAGE", "Привет, мир!")

    if chat_id is None:
        raise ValueError("CHAT_ID environment variable is not set")

    async with Bot(token=token) as bot:
        await bot.send_message(chat_id=int(chat_id), text=message)


if __name__ == "__main__":
    asyncio.run(main())
