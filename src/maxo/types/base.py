from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, ClassVar, Self, dataclass_transform

from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError

if TYPE_CHECKING:
    from maxo.bot.bot import Bot


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
        # `get`, not `pop`: `type.__new__` must fill the cell before
        # `dataclass` runs, Python 3.14.0-3.14.4 crashes on an empty one.
        classcell = namespace.get("__classcell__")
        class_: type = super().__new__(cls, name, bases, namespace, **kwargs)
        # `dataclass(slots=True)` re-creates the class through this metaclass
        # with `__slots__` set: don't wrap it twice.
        if "__slots__" in namespace:
            return class_

        data_class: type = dataclass(slots=slots, kw_only=True)(class_)

        # `dataclass` takes field defaults via `getattr`,
        # so an attribute of a plain base would silently become one
        plain_bases = [base for base in class_.__mro__ if not is_dataclass(base)]
        for field_ in fields(class_):
            for base in plain_bases:
                if field_.name in vars(base):
                    msg = (
                        f"{class_.__name__}.{field_.name} gets its default from "
                        f"{base.__name__}.{field_.name}; declare it there "
                        "under `if TYPE_CHECKING:` only"
                    )
                    raise TypeError(msg)

        # `slots=True` returns a new class, but `super()` in its methods still
        # points to the old one. Python < 3.13.14 doesn't fix it itself.
        if classcell is not None:
            classcell.cell_contents = data_class
        return data_class


class MaxoType(metaclass=_MaxoTypeMetaClass):
    """
    База всех dataclass'ов maxo. Бота не хранит.

    Наследники сами становятся `@dataclass(slots=True, kw_only=True)`;
    `class X(MaxoType, slots=False)` отключает слоты.
    """


class FacadeMaxoType(MaxoType):
    """
    Тип, который хранит бота: апдейты и сообщения.

    `_bot` - поле dataclass, поэтому `dataclasses.replace` и `copy` его
    сохраняют.
    """

    _bot: "Bot | None" = field(default=None, repr=False, compare=False)

    @property
    def bot(self) -> "Bot":
        if self._bot is not None:
            return self._bot

        raise AttributeIsEmptyError(
            obj=self,
            attr="bot",
        )

    def as_(self, bot: "Bot | None") -> Self:
        """Привязывает бота к себе и ко всем вложенным `FacadeMaxoType`."""
        from maxo.types.binding import bind_bot  # noqa: PLC0415

        return bind_bot(self, bot)


class BaseUpdate(MaxoType):
    """Событие роутинга: апдейт MAX, сигнал или ошибка."""


class MaxUpdate(BaseUpdate, FacadeMaxoType):
    """
    Базовый класс для всех апдейтов из Макса.

    У всех апдейтов есть тип (`type`, `update_type`) и время (`timestamp`).
    Методы для работы с апдейтом (например, отправить сообщение или ответить
    на колбэк) подмешаны в сам апдейт через `*MethodsFacade`.
    """

    type: ClassVar[UpdateType]
    timestamp: datetime

    @property
    def update_type(self) -> UpdateType:
        return self.type
