from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from maxo.types import base
from maxo.types.base import MaxoType


def test_facade_property_cannot_become_field_default() -> None:
    class Facade:
        @property
        def chat_id(self) -> int:
            return 0

    with pytest.raises(TypeError, match=r"Host\.chat_id .* Facade\.chat_id"):

        class Host(MaxoType, Facade):
            chat_id: int


class _Greeter(MaxoType):
    def greet(self) -> str:
        return "base"


class _Slotted(_Greeter):
    x: int = 1

    def greet(self) -> str:
        return "slotted+" + super().greet()


class _NotSlotted(_Slotted, slots=False):
    def greet(self) -> str:
        return "plain+" + super().greet()


class _OwnSlots(_Greeter):
    __slots__ = ("x",)

    def greet(self) -> str:
        return "own+" + super().greet()


def test_slots_flag() -> None:
    assert not hasattr(_Slotted(), "__dict__")
    assert hasattr(_NotSlotted(), "__dict__")


@pytest.mark.parametrize(
    ("class_", "greeting"),
    [
        (_Slotted, "slotted+base"),
        (_NotSlotted, "plain+slotted+base"),
        (_OwnSlots, "own+base"),
    ],
)
def test_zero_arg_super(class_: type[_Greeter], greeting: str) -> None:
    assert class_().greet() == greeting


def test_class_cell_is_filled_before_dataclass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Python 3.14.0-3.14.4 `dataclass` crashes on an empty `__class__` cell;
    # newer patches don't, so check the cell directly.
    wrapped: list[type] = []

    def spy(**kwargs: Any) -> Callable[[type], type]:  # Any: dataclass kwargs
        def wrap(class_: type) -> type:
            greet = vars(class_)["greet"]
            cell = greet.__closure__[greet.__code__.co_freevars.index("__class__")]
            assert cell.cell_contents is class_
            wrapped.append(class_)
            return dataclass(**kwargs)(class_)

        return wrap

    monkeypatch.setattr(base, "dataclass", spy)

    class Child(_Greeter):
        def greet(self) -> str:
            return "child+" + super().greet()

    assert wrapped
    assert Child().greet() == "child+base"
