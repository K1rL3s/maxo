from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.bot_command import BotCommand


class BotCommandsInfo(MaxoType):
    """
    Информация о командах бота

    Args:
        commands: Команды, которые поддерживает бот
    """

    commands: Omittable[list[BotCommand]] = Omitted()
    """Команды, которые поддерживает бот"""

    @property
    def unsafe_commands(self) -> list[BotCommand]:
        if is_defined(self.commands):
            return self.commands

        raise AttributeIsEmptyError(
            obj=self,
            attr="commands",
        )
