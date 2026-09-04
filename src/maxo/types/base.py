from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, dataclass_transform

from maxo.enums.update_type import UpdateType
from maxo.types.facades.base import BaseMethodsFacade


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
