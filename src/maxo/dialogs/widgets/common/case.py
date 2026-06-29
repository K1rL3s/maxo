from collections.abc import Callable, Hashable
from typing import Any, TypeVar

from maxo.dialogs import DialogManager
from maxo.dialogs.integrations.magic_filter import DialogMagic

T = TypeVar("T")
Selector = Callable[[dict[Any, Any], T, DialogManager], Hashable]


def new_case_field(fieldname: str) -> Selector[T]:
    def case_field(
        data: dict[Any, Any],
        widget: T,
        manager: DialogManager,
    ) -> Hashable:
        return data.get(fieldname)

    return case_field


def new_magic_selector(f: DialogMagic) -> Selector[T]:
    def when_magic(
        data: dict[Any, Any],
        widget: T,
        manager: DialogManager,
    ) -> bool:
        return f.resolve(data)

    return when_magic
