from collections.abc import (
    Generator,
    Iterable,
    MutableSequence,
    Sequence,
)
from copy import deepcopy
from itertools import chain, cycle
from typing import ClassVar, Self, TypeVar

from maxo.omit import Omittable, Omitted
from maxo.types import ClipboardButton, OpenAppButton
from maxo.types.buttons import InlineButtons
from maxo.types.callback_button import CallbackButton
from maxo.types.link_button import LinkButton
from maxo.types.message_button import MessageButton
from maxo.types.request_contact_button import RequestContactButton
from maxo.types.request_geo_location_button import RequestGeoLocationButton

T = TypeVar("T")


def repeat_last(items: Iterable[T]) -> Generator[T, None, None]:
    items_iter = iter(items)

    try:
        value = next(items_iter)
    except StopIteration:
        return

    yield value

    finished = False
    while True:
        if not finished:
            try:
                value = next(items_iter)
            except StopIteration:
                finished = True
        yield value


class KeyboardValidator:
    max_width: ClassVar[int] = 7
    min_width: ClassVar[int] = 1
    max_buttons: ClassVar[int] = 210

    def validate_keyboard(self, markup: Sequence[Sequence[InlineButtons]]) -> bool:
        count = 0
        for row in markup:
            self.validate_row(row)
            count += len(row)
        if count > self.max_buttons:
            raise ValueError(
                f"Too much buttons detected Max allowed count - {self.max_buttons}",
            )
        return True

    def validate_row(self, row: Sequence[InlineButtons]) -> None:
        if len(row) > self.max_width:
            raise ValueError(f"Row {row!r} is too long (max width: {self.max_width})")

    def validate_size(self, size: int) -> int:
        if size not in range(self.min_width, self.max_width + 1):
            raise ValueError(
                f"Row size {size} is not allowed, "
                f"range: [{self.min_width}, {self.max_width}]",
            )
        return size


class KeyboardBuilder:
    _keyboard: MutableSequence[MutableSequence[InlineButtons]]

    __slots__ = ("_keyboard", "_validator")

    def __init__(
        self,
        keyboard: MutableSequence[MutableSequence[InlineButtons]] | None = None,
    ) -> None:
        validator = KeyboardValidator()

        if keyboard:
            validator.validate_keyboard(keyboard)
        else:
            keyboard = []

        self._keyboard = keyboard
        self._validator = validator

    def add_callback(self, text: str, payload: str) -> Self:
        return self.add(CallbackButton(text=text, payload=payload))

    def add_link(self, text: str, url: str) -> Self:
        return self.add(LinkButton(text=text, url=url))

    def add_request_contact(self, text: str) -> Self:
        return self.add(RequestContactButton(text=text))

    def add_request_geo_location(
        self,
        text: str,
        quick: Omittable[bool] = Omitted(),
    ) -> Self:
        return self.add(RequestGeoLocationButton(text=text, quick=quick))

    def add_message(self, text: str) -> Self:
        return self.add(MessageButton(text=text))

    def add_clipboard(self, text: str, payload: str) -> Self:
        return self.add(ClipboardButton(text=text, payload=payload))

    def add_open_app(
        self,
        text: str,
        contact_id: Omittable[int] = Omitted(),
        payload: Omittable[str] = Omitted(),
        *,
        web_app: str,
    ) -> Self:
        return self.add(
            OpenAppButton(
                text=text,
                contact_id=contact_id,
                payload=payload,
                web_app=web_app,
            ),
        )

    @property
    def buttons(self) -> Generator[InlineButtons, None, None]:
        yield from chain.from_iterable(self.build())

    def build(self) -> MutableSequence[MutableSequence[InlineButtons]]:
        return deepcopy(self._keyboard)

    def add(self, *buttons: InlineButtons) -> Self:
        keyboard = self.build()

        if keyboard and len(keyboard[-1]) < self._validator.max_width:
            last_row = keyboard[-1]
            pos = self._validator.max_width - len(last_row)
            head, buttons = buttons[:pos], buttons[pos:]
            last_row.extend(head)

        if self._validator.max_width > 0:
            while buttons:
                row, buttons = (
                    buttons[: self._validator.max_width],
                    buttons[self._validator.max_width :],
                )
                keyboard.append(list(row))
        else:
            keyboard.append(list(buttons))

        self._keyboard = keyboard
        return self

    def row(self, *buttons: InlineButtons, width: int | None = None) -> Self:
        if width is None:
            width = self._validator.max_width

        self._validator.validate_size(width)
        self._validator.validate_row(buttons)
        self._keyboard.extend(
            list(buttons[pos : pos + width]) for pos in range(0, len(buttons), width)
        )
        return self

    def adjust(self, *sizes: int, repeat: bool = False) -> Self:
        if not sizes:
            sizes = (self._validator.max_width,)

        validated_sizes = map(self._validator.validate_size, sizes)
        sizes_iter = cycle(validated_sizes) if repeat else repeat_last(validated_sizes)
        size = next(sizes_iter)

        keyboard = []
        row: MutableSequence[InlineButtons] = []
        for button in self.buttons:
            if len(row) >= size:
                keyboard.append(row)
                size = next(sizes_iter)
                row = []
            row.append(button)
        if row:
            keyboard.append(row)

        self._keyboard = keyboard

        return self

    def attach(self, builder: "KeyboardBuilder") -> "KeyboardBuilder":
        self._keyboard.extend(builder.build())
        return self
