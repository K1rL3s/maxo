import itertools

import pytest

from maxo.types.callback_button import CallbackButton
from maxo.types.link_button import LinkButton
from maxo.types.open_app_button import OpenAppButton
from maxo.utils.builders import KeyboardBuilder


@pytest.fixture
def keyboard_builder() -> KeyboardBuilder:
    return KeyboardBuilder()


def test_init_empty(keyboard_builder: KeyboardBuilder) -> None:
    assert keyboard_builder.build() == []


def test_add_single_button(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add_callback("Test", "payload")

    keyboard = keyboard_builder.build()

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 1
    assert keyboard[0][0] == CallbackButton(text="Test", payload="payload")


def test_add_multiple_buttons_same_row(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add(
        CallbackButton(text="1", payload="1"),
        CallbackButton(text="2", payload="2"),
        CallbackButton(text="3", payload="3"),
    )

    keyboard = keyboard_builder.build()

    assert len(keyboard) == 1
    assert len(keyboard[0]) == 3


def test_add_creates_new_row_after_max_width(keyboard_builder: KeyboardBuilder) -> None:
    buttons = [CallbackButton(text=str(i), payload=str(i)) for i in range(8)]

    keyboard_builder.add(*buttons)

    keyboard = keyboard_builder.build()

    assert len(keyboard) == 2
    assert len(keyboard[0]) == 7
    assert len(keyboard[1]) == 1


def test_row_with_custom_width(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.row(
        *[CallbackButton(text=str(i), payload=str(i)) for i in range(5)],
        width=2,
    )

    keyboard = keyboard_builder.build()

    assert [len(row) for row in keyboard] == [2, 2, 1]


def test_adjust_default(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add(
        *[CallbackButton(text=str(i), payload=str(i)) for i in range(10)],
    )

    keyboard_builder.adjust()

    keyboard = keyboard_builder.build()

    assert [len(row) for row in keyboard] == [7, 3]


def test_adjust_sizes(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add(
        *[CallbackButton(text=str(i), payload=str(i)) for i in range(6)],
    )

    keyboard_builder.adjust(2, 3)

    keyboard = keyboard_builder.build()

    assert [len(row) for row in keyboard] == [2, 3, 1]


def test_adjust_repeat(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add(
        *[CallbackButton(text=str(i), payload=str(i)) for i in range(8)],
    )

    keyboard_builder.adjust(2, 3, repeat=True)

    keyboard = keyboard_builder.build()

    assert [len(row) for row in keyboard] == [2, 3, 2, 1]


def test_attach() -> None:
    first = KeyboardBuilder()
    second = KeyboardBuilder()

    first.add_callback("1", "1")
    second.add_callback("2", "2")

    first.attach(second)

    keyboard = first.build()

    assert len(keyboard) == 2
    assert keyboard[0][0] == CallbackButton(text="1", payload="1")
    assert keyboard[1][0] == CallbackButton(text="2", payload="2")


def test_build_returns_copy(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add_callback("Test", "payload")

    keyboard = keyboard_builder.build()
    keyboard[0].append(CallbackButton(text="Other", payload="other"))

    assert len(keyboard_builder.build()) == 1
    assert len(keyboard_builder.build()[0]) == 1


def test_buttons_property(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add_callback("1", "1")
    keyboard_builder.add_link("2", "https://example.com")

    buttons = list(keyboard_builder.buttons)

    assert buttons == [
        CallbackButton(text="1", payload="1"),
        LinkButton(text="2", url="https://example.com"),
    ]


@pytest.mark.parametrize("width", [0, 8, -1])
def test_row_invalid_width(
    keyboard_builder: KeyboardBuilder,
    width: int,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"Row size -?\d+ is not allowed, range: \[1, 7\]",
    ):
        keyboard_builder.row(
            CallbackButton(text="1", payload="1"),
            width=width,
        )


def test_add_too_many_buttons_in_single_call(keyboard_builder: KeyboardBuilder) -> None:
    buttons = [CallbackButton(text=str(i), payload=str(i)) for i in range(10)]

    keyboard_builder.add(*buttons)

    keyboard = keyboard_builder.build()

    assert len(list(itertools.chain.from_iterable(keyboard))) == 10
    assert [len(row) for row in keyboard] == [7, 3]


def test_constructor_invalid_keyboard() -> None:
    with pytest.raises(ValueError, match=r"Row .* is too long \(max width: 7\)"):
        KeyboardBuilder(
            keyboard=[[CallbackButton(text=str(i), payload=str(i)) for i in range(8)]],
        )


def test_return_self(keyboard_builder: KeyboardBuilder) -> None:
    assert keyboard_builder.add() is keyboard_builder
    assert keyboard_builder.row() is keyboard_builder
    assert keyboard_builder.adjust(1) is keyboard_builder
    assert keyboard_builder.add_callback("1", "1") is keyboard_builder
    assert keyboard_builder.add_message("1") is keyboard_builder
    assert keyboard_builder.add_link("1", "1") is keyboard_builder
    assert keyboard_builder.add_open_app("1", web_app="1") is keyboard_builder
    assert keyboard_builder.add_request_geo_location("1") is keyboard_builder
    assert keyboard_builder.add_request_contact("1") is keyboard_builder
    assert keyboard_builder.add_clipboard("1", "1") is keyboard_builder

    another_builder = KeyboardBuilder()
    assert keyboard_builder.attach(another_builder) is keyboard_builder


def test_add_open_app_keeps_positional_order(keyboard_builder: KeyboardBuilder) -> None:
    keyboard_builder.add_open_app("App", 5, "start", web_app="bot")

    assert keyboard_builder.build() == [
        [OpenAppButton(text="App", contact_id=5, payload="start", web_app="bot")],
    ]
