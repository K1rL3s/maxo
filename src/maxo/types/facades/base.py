from typing import TYPE_CHECKING, Optional, Self

from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined

if TYPE_CHECKING:
    from maxo import Bot


class BaseMethodsFacade:
    """
    Базовый фасад: хранит ссылку на бота и отдаёт её наследникам.

    От него растёт вся цепочка фасадов (`BotMethodsFacade` ->
    `ChatMethodsFacade` -> ...). Он же подмешан в `MaxoType`, поэтому любой тип
    несёт `bot`/`as_` (это наследование со временем уберём - бот на типе нужен
    не всем).

    Не наследуется от `ABC`/`Protocol`: `MaxoType` сделан через метакласс, а он
    конфликтует с `ABCMeta` в апдейтах. См. историю в
    https://github.com/K1rL3s/maxo/pull/103 и .../pull/107.
    """

    __slots__ = ("_bot",)

    def __init__(self, bot: Optional["Bot"] = None) -> None:
        self._bot = bot

    @property
    def bot(self) -> "Bot":
        if is_defined(self._bot):
            return self._bot

        raise AttributeIsEmptyError(
            obj=self,
            attr="_bot",
        )

    @bot.setter
    def bot(self, bot: Optional["Bot"]) -> None:
        self._bot = bot

    def as_(self, bot: Optional["Bot"]) -> Self:
        self.bot = bot
        return self
