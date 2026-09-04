from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Self, dataclass_transform

from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined

if TYPE_CHECKING:
    from maxo import Bot


@dataclass_transform(
    frozen_default=False,
    kw_only_default=True,
)
class _MaxoTypeMetaClass(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[Any, ...],
        namespace: dict[str, Any],
        slots: bool = True,
        **kwargs: Any,
    ) -> Any:
        class_ = super().__new__(cls, name, bases, namespace, **kwargs)
        if "__slots__" in namespace:
            return class_

        return dataclass(
            slots=slots,
            frozen=False,
            kw_only=True,
        )(class_)


class BaseMaxoType(metaclass=_MaxoTypeMetaClass):
    pass


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


# TODO: `MaxoType` наследует `BaseMethodsFacade` только ради слота `_bot` -
# `bot`/`as_` не нужны большинству DTO (`User`, `Chat`, ...). Убрать это
# наследование можно, сузив `_load_bot` в `serialization` до фасад-типов.
#
# Отдельная, большая проблема: `*MethodsFacade` подмешаны прямо в типы апдейтов
# (`class BotStarted(MaxUpdate, ChatMethodsFacade)`), а те под метаклассом,
# который конфликтует с `ABCMeta`. Поэтому фасады не могут быть ABC - отсюда
# декоративные `@abstractmethod`, раздвоённые `if TYPE_CHECKING`-объявления полей
# и `type: ignore[misc]` на апдейтах. Это лечится только выносом фасада из базы
# типа (отдельный объект `update.facade` или `Protocol`), не строкой ниже.
class MaxoType(BaseMaxoType, BaseMethodsFacade):
    def __post_init__(self) -> None:
        BaseMethodsFacade.__init__(self)


class BaseUpdate(MaxoType):
    pass


class MaxUpdate(BaseUpdate):
    """
    Базовый класс для всех апдейтов из Макса.

    У всех апдейтов есть тип (`type`, `update_type`) и время (`timestamp`).
    Фасад (`facade`) объединяет методы для работы с апдейтом,
    например, отправить сообщение или ответить на колбэк.
    """

    type: ClassVar[UpdateType]
    timestamp: datetime

    @property
    def update_type(self) -> UpdateType:
        return self.type
