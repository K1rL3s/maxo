from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.bot_command import BotCommand
from maxo.types.user_with_photo import UserWithPhoto


class BotInfo(UserWithPhoto):
    """
    Объект включает общую информацию о боте, URL аватара и описание. Является наследником [схемы UserWithPhoto](https://dev.max.ru/docs-api/objects/UserWithPhoto). Дополнительно к ней содержит список команд, поддерживаемых ботом. Возвращается только при вызове метода `GET /me`

    Args:
        commands: Команды, поддерживаемые ботом
    """

    commands: Omittable[list[BotCommand] | None] = Omitted()
    """Команды, поддерживаемые ботом"""

    @property
    def unsafe_commands(self) -> list[BotCommand]:
        if is_defined(self.commands):
            return self.commands

        raise AttributeIsEmptyError(
            obj=self,
            attr="commands",
        )
