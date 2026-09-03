from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, dataclass_transform

from maxo.enums.update_type import UpdateType


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


class MaxoType(BaseMaxoType):
    pass


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
