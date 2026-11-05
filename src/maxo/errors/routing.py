from collections.abc import Sequence
from typing import TYPE_CHECKING

from maxo.errors.base import MaxoError

if TYPE_CHECKING:
    from maxo.routing.interfaces.router import BaseRouter


class CycleRoutersError(MaxoError):
    routers: Sequence["BaseRouter"]

    def __str__(self) -> str:
        details = self._render_details()
        return f"Cycle routers detected.\n{details}"

    def _render_details(self) -> str:
        routers = self.routers

        if len(routers) == 1:
            return f"⥁ {routers[0]}"

        details = "╭─>─╮\n"
        start = True
        for router in routers:
            if not start:
                details += "│   ▼\n"
            details += f"│ {router}\n"
            start = False

        details += "╰─<─╯"

        return details


class RouterAlreadyIncludedError(MaxoError):
    router: "BaseRouter"
    parent_router: "BaseRouter"

    def __str__(self) -> str:
        return f"{self.router} is already included into {self.parent_router}"
