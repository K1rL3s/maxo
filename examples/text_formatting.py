import logging
import os

from maxo import Bot, Dispatcher
from maxo.enums import TextFormat
from maxo.routing.filters import Command
from maxo.routing.updates import MessageCreated
from maxo.transport.long_polling import LongPolling
from maxo.utils.formatting import (
    Bold,
    Heading,
    Highlighted,
    Italic,
    Link,
    Mention,
    Monospaced,
    Strikethrough,
    Text,
    Underline,
    as_list,
    as_marked_list,
    as_numbered_list,
)

bot = Bot(os.environ["TOKEN"])
dp = Dispatcher()


@dp.message_created(Command("start"))
async def start_handler(update: MessageCreated) -> None:
    text = Text(
        Heading("Привет, это демонстрация возможностей форматирования текста."),
        "\n\n",
        Bold("Это жирный текст."),
        "\n",
        Italic("Это курсивный текст."),
        "\n",
        Underline("Это подчеркнутый текст."),
        "\n",
        Strikethrough("Это зачеркнутый текст."),
        "\n",
        Monospaced("Это моноширинный текст."),
        "\n",
        Link("Это ссылка на библиотеку maxo.", url="https://github.com/K1rL3s/maxo"),
        "\n",
        "Это упоминание пользователя: ",
        Mention(
            update.message.unsafe_sender.fullname,
            user_id=update.message.unsafe_sender.id,
        ),
        "\n",
        Highlighted("Это выделенный текст"),
        "\n\n",
        "Вы также можете использовать вспомогательные функции для создания списков:",
        "\n\n",
        as_list(
            "Простой список:",
            "Элемент 1",
            "Элемент 2",
            "Элемент 3",
        ),
        "\n\n",
        as_marked_list(
            "Маркированный список:",
            "Элемент 1",
            "Элемент 2",
            "Элемент 3",
        ),
        "\n\n",
        as_numbered_list(
            "Нумерованный список:",
            "Элемент 1",
            "Элемент 2",
            "Элемент 3",
            start=4,
        ),
    )

    await update.answer_text(text.as_html(), format=TextFormat.HTML)
    await update.answer_text(text.as_markdown(), format=TextFormat.MARKDOWN)


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
