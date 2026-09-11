from typing import TYPE_CHECKING, Optional, Self

from maxo.errors import AttributeIsEmptyError

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


class BaseMethodsFacade:
    """
    Единственный держатель бота: слот `_bot` + `bot`/`as_`.

    От него растёт вся цепочка фасадов (`BotMethodsFacade` ->
    `ChatMethodsFacade` -> ...), и он же подмешан в `MaxoType`. Обход дерева и
    простановку бота делает `bind_bot` (см. `types/binding.py`).
    """

    __slots__ = ("_bot",)

    def __init__(self, bot: Optional["Bot"] = None) -> None:
        self._bot = bot

    def __post_init__(self) -> None:
        self._bot = None

    @property
    def bot(self) -> "Bot":
        if self._bot is not None:
            return self._bot

        raise AttributeIsEmptyError(
            obj=self,
            attr="_bot",
        )

    @bot.setter
    def bot(self, bot: Optional["Bot"]) -> None:
        from maxo.types.binding import bind_bot  # noqa: PLC0415

        bind_bot(self, bot)

    def as_(self, bot: Optional["Bot"]) -> Self:
        from maxo.types.binding import bind_bot  # noqa: PLC0415

        bind_bot(self, bot)
        return self
