from typing import Any

from maxo.dialogs.api.internal import RawKeyboard
from maxo.dialogs.api.protocols import DialogManager, DialogProtocol
from maxo.dialogs.widgets.common import (
    BaseScroll,
    OnPageChangedVariants,
    WhenCondition,
)
from maxo.types import Callback, CallbackButton

from .base import Keyboard
from .group import Group


class ScrollingGroup(Group, BaseScroll):
    def __init__(
        self,
        *buttons: Keyboard,
        id: str,
        width: int | None = None,
        height: int = 0,
        when: WhenCondition = None,
        on_page_changed: OnPageChangedVariants = None,
        hide_on_single_page: bool = False,
        hide_pager: bool = False,
    ) -> None:
        Group.__init__(self, *buttons, id=id, width=width, when=when)
        BaseScroll.__init__(self, id=id, on_page_changed=on_page_changed)
        self.height = height
        self.hide_on_single_page = hide_on_single_page
        self.hide_pager = hide_pager

    def _get_page_count(
        self,
        keyboard: RawKeyboard,
    ) -> int:
        return len(keyboard) // self.height + bool(len(keyboard) % self.height)

    async def _render_contents(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        return await super()._render_keyboard(data, manager)

    async def _render_pager(
        self,
        pages: int,
        manager: DialogManager,
    ) -> RawKeyboard:
        if self.hide_pager:
            return []
        if pages == 0 or (pages == 1 and self.hide_on_single_page):
            return []

        last_page = pages - 1
        current_page = min(last_page, await self.get_page(manager))
        next_page = min(last_page, current_page + 1)
        prev_page = max(0, current_page - 1)

        return [
            [
                CallbackButton(
                    text="1",
                    payload=self._item_payload("0"),
                ),
                CallbackButton(
                    text="<",
                    payload=self._item_payload(prev_page),
                ),
                CallbackButton(
                    text=str(current_page + 1),
                    payload=self._item_payload(current_page),
                ),
                CallbackButton(
                    text=">",
                    payload=self._item_payload(next_page),
                ),
                CallbackButton(
                    text=str(last_page + 1),
                    payload=self._item_payload(last_page),
                ),
            ],
        ]

    async def _render_page(
        self,
        page: int,
        keyboard: list[list[CallbackButton]],
    ) -> list[list[CallbackButton]]:
        pages = self._get_page_count(keyboard)
        last_page = pages - 1
        current_page = min(last_page, page)
        page_offset = current_page * self.height

        return keyboard[page_offset : page_offset + self.height]

    async def _render_keyboard(
        self,
        data: dict[Any, Any],
        manager: DialogManager,
    ) -> RawKeyboard:
        keyboard = await self._render_contents(data, manager)
        pages = self._get_page_count(keyboard)

        pager = await self._render_pager(pages, manager)
        page_keyboard = await self._render_page(
            page=await self.get_page(manager),
            keyboard=keyboard,
        )

        return page_keyboard + pager

    async def _process_item_callback(
        self,
        callback: Callback,
        data: str,
        dialog: DialogProtocol,
        manager: DialogManager,
    ) -> bool:
        await self.set_page(callback, int(data), manager)
        return True

    async def get_page_count(self, data: dict[Any, Any], manager: DialogManager) -> int:
        keyboard = await self._render_contents(data, manager)
        return self._get_page_count(keyboard=keyboard)
