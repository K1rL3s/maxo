import logging
import os

from maxo import Bot, Dispatcher
from maxo.errors import MaxoError
from maxo.routing.filters import Command, ExceptionTypeFilter
from maxo.routing.updates import ErrorEvent, MessageCreated
from maxo.transport.long_polling import LongPolling

logger = logging.getLogger(__name__)

dp = Dispatcher()


class InvalidAge(MaxoError):
    message: str


class InvalidName(ValueError):
    pass


@dp.error(ExceptionTypeFilter(InvalidAge))
async def handle_invalid_age_exception(
    event: ErrorEvent[InvalidAge, MessageCreated],
) -> None:
    """Сюда попадают только ошибки с типом InvalidAge."""
    assert isinstance(event.error, InvalidAge)  # noqa: S101
    logger.error("Error caught: %r while processing %r", event.error, event.update)
    text = f"Поймана ошибка: {event.error!r}"
    await event.event.answer_text(text)


@dp.error()
async def handle_invalid_exceptions(
    event: ErrorEvent[Exception, MessageCreated],
) -> None:
    """Обработчик всех остальных ошибок (без фильтра по типу)."""
    logger.error(
        "Unhandled error caught: %r while processing %r",
        event.error,
        event.update,
    )
    text = f"Произошла неизвестная ошибка: {event.error!r}"
    await event.event.answer_text(text)


@dp.message_created(Command("age"))
async def handle_set_age(message: MessageCreated) -> None:
    """
    Обрабатывает только сообщения с командой /age.
    Если пользователь отправил /age с неверным возрастом, выбрасывается InvalidAge -
    его ловит handle_invalid_age_exception.
    Объект команды: keyword `command`, тип CommandObject; аргументы: command.args.
    """
    age = (
        message.message.body.text.split(" ", 1)[1]
        if message.message.body.text and " " in message.message.body.text
        else None
    )
    if not age:
        msg = "Возраст не указан. Пожалуйста, укажи свой возраст аргументом команды."
        raise InvalidAge(msg)
    if not age.isdigit():
        msg = "Возраст должен быть числом"
        raise InvalidAge(msg)
    age = int(age)
    await message.reply_text(text=f"Твой возраст: {age}")


@dp.message_created(Command("name"))
async def handle_set_name(message: MessageCreated) -> None:
    """
    Обрабатывает только сообщения с командой /name.
    Объект команды: аргумент keyword `command` с типом CommandObject.
    Аргументы команды: свойство command.args.
    """
    name = (
        message.message.body.text.split(" ", 1)[1]
        if message.message.body.text and " " in message.message.body.text
        else None
    )
    if not name:
        msg = "Неверное имя. Укажи своё имя аргументом команды (например: /name Имя)."
        raise InvalidName(msg)
    await message.reply_text(text=f"Тебя зовут {name}")


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    bot = Bot(token=os.environ["TOKEN"])
    LongPolling(dp).run(bot)


if __name__ == "__main__":
    main()
