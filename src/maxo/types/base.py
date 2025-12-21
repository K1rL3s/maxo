from dataclasses import dataclass
from typing import Any, dataclass_transform


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


class MaxoType(metaclass=_MaxoTypeMetaClass):
    pass
