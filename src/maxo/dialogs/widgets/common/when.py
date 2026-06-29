from abc import abstractmethod
from typing import Any, Protocol

from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.integrations.magic_filter import DialogMagic


class Predicate(Protocol):
    @abstractmethod
    def __call__(
        self,
        data: dict[Any, Any],
        widget: "Whenable",
        dialog_manager: DialogManager,
        /,
    ) -> bool:
        """
        Check if widget should be shown.

        :param data: Data received from getter
        :param widget: Widget we are working with
        :param dialog_manager: Dialog manager to access current context
        :return: ``True`` if widget has to be shown, ``False`` otherwise
        """
        raise NotImplementedError


WhenCondition = str | DialogMagic | Predicate | None


def new_when_field(fieldname: str) -> Predicate:
    def when_field(
        data: dict[Any, Any],
        widget: "Whenable",
        manager: DialogManager,
    ) -> bool:
        return bool(data.get(fieldname))

    return when_field


def new_when_magic(f: DialogMagic) -> Predicate:
    def when_magic(
        data: dict[Any, Any],
        widget: "Whenable",
        manager: DialogManager,
    ) -> bool:
        return f.resolve(data)

    return when_magic


def true_condition(
    data: dict[Any, Any],
    widget: "Whenable",
    manager: DialogManager,
) -> bool:
    return True


class Whenable:
    def __init__(self, when: WhenCondition = None) -> None:
        self.condition: Predicate
        if when is None:
            self.condition = true_condition
        elif isinstance(when, str):
            self.condition = new_when_field(when)
        elif isinstance(when, DialogMagic):
            self.condition = new_when_magic(when)
        else:
            self.condition = when

    def is_(self, data: dict[Any, Any], manager: DialogManager) -> bool:
        return self.condition(data, self, manager)
