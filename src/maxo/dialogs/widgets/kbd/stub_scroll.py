from collections.abc import Callable
from typing import Any

from maxo.dialogs.api.internal import RawKeyboard
from maxo.dialogs.api.protocols import DialogManager
from maxo.dialogs.integrations.magic_filter import DialogMagic
from maxo.dialogs.widgets.common.scroll import BaseScroll, OnPageChangedVariants

from .base import Keyboard

PagesGetter = Callable[[dict, "StubScroll", DialogManager], int]


def new_pages_field(fieldname: str) -> PagesGetter:
    def pages_field(
        data: dict[Any, Any],
        widget: "StubScroll",
        manager: DialogManager,
    ) -> int:
        return data.get(fieldname)

    return pages_field


def new_pages_magic(f: DialogMagic) -> PagesGetter:
    def pages_magic(
        data: dict[Any, Any],
        widget: "StubScroll",
        manager: DialogManager,
    ) -> int:
        return f.resolve(data)

    return pages_magic


def new_pages_fixed(pages: int) -> PagesGetter:
    def pages_fixed(
        data: dict[Any, Any],
        widget: "StubScroll",
        manager: DialogManager,
    ) -> int:
        return pages

    return pages_fixed


class StubScroll(Keyboard, BaseScroll):
    def __init__(
        self,
        id: str,
        pages: str | int | PagesGetter | DialogMagic,
        on_page_changed: OnPageChangedVariants = None,
    ) -> None:
        Keyboard.__init__(self, id=id, when=None)
        BaseScroll.__init__(self, id=id, on_page_changed=on_page_changed)
        if isinstance(pages, str):
            self._pages = new_pages_field(pages)
        elif isinstance(pages, DialogMagic):
            self._pages = new_pages_magic(pages)
        else:
            self._pages = new_pages_fixed(pages)

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return [[]]

    async def get_page_count(self, data: dict[Any, Any], manager: DialogManager) -> int:
        return self._pages(data, self, manager)
