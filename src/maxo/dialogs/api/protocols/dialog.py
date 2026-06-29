from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Protocol, runtime_checkable

from maxo.dialogs.api.entities import Data, LaunchMode, NewMessage
from maxo.fsm import State, StatesGroup

from .manager import DialogManager

if TYPE_CHECKING:
    from maxo.dialogs.api.internal.widgets import Widget


class CancelEventProcessing(Exception):
    pass


@runtime_checkable
class DialogProtocol(Protocol):
    @property
    def launch_mode(self) -> LaunchMode:
        raise NotImplementedError

    @abstractmethod
    def states_group_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def states(self) -> list[State]:
        raise NotImplementedError

    @abstractmethod
    def states_group(self) -> type[StatesGroup]:
        raise NotImplementedError

    @abstractmethod
    async def process_close(
        self,
        result: Any,
        manager: DialogManager,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def process_start(
        self,
        manager: "DialogManager",
        start_data: Data,
        state: State | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def process_result(
        self,
        start_data: Data,
        result: Any,
        manager: "DialogManager",
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def find(self, widget_id: str) -> Optional["Widget"]:
        raise NotImplementedError

    @abstractmethod
    async def load_data(
        self,
        manager: DialogManager,
    ) -> dict[Any, Any]:
        raise NotImplementedError

    @abstractmethod
    async def render(self, manager: DialogManager) -> NewMessage:
        raise NotImplementedError
