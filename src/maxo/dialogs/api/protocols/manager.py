from abc import abstractmethod
from contextlib import AbstractAsyncContextManager
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Protocol

from maxo import Bot
from maxo.dialogs.api.entities import (
    AccessSettings,
    ChatEvent,
    Context,
    Data,
    ShowMode,
    Stack,
    StartMode,
)
from maxo.enums import ChatType
from maxo.fsm import State

if TYPE_CHECKING:
    from maxo.dialogs.api.internal.widgets import Widget


class UnsetId(Enum):
    UNSET = "UNSET"


class BaseDialogManager(Protocol):
    @abstractmethod
    async def done(
        self,
        result: Any = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        """Закрыть текущий диалог и показать нижележащий в стеке."""
        raise NotImplementedError

    @abstractmethod
    async def start(
        self,
        state: State,
        data: Data = None,
        mode: StartMode = StartMode.NORMAL,
        show_mode: ShowMode | None = None,
        access_settings: AccessSettings | None = None,
    ) -> None:
        """Добавить новый диалог в стек и показать его."""
        raise NotImplementedError

    @abstractmethod
    async def switch_to(
        self,
        state: State,
        show_mode: ShowMode | None = None,
    ) -> None:
        """Переключить активное окно в текущем диалоге."""
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        data: dict[Any, Any] | None = None,
        show_mode: ShowMode | None = None,
    ) -> None:
        """Обновить данные диалога и перерисовать текущее окно."""
        raise NotImplementedError

    @abstractmethod
    def bg(
        self,
        user_id: int | None = None,
        chat_id: int | None = None,
        stack_id: str | None = None,
        load: bool = False,  # load chat and user
    ) -> "BaseDialogManager":
        """Получить фоновый менеджер для указанного чата."""
        raise NotImplementedError

    @abstractmethod
    def fg(self) -> AbstractAsyncContextManager["DialogManager"]:
        """Получить полнофункциональный менеджер диалога."""
        raise NotImplementedError


class BgManagerFactory(Protocol):
    @abstractmethod
    def bg(
        self,
        bot: Bot,
        user_id: int,
        chat_id: int,
        stack_id: str | None = None,
        load: bool = False,  # load chat and user
        chat_type: ChatType = ChatType.CHAT,
    ) -> "BaseDialogManager":
        """Получить фоновый менеджер для указанного чата."""
        raise NotImplementedError


class DialogManager(BaseDialogManager, Protocol):
    @property
    @abstractmethod
    def event(self) -> ChatEvent:
        raise NotImplementedError

    @abstractmethod
    async def mark_closed(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def middleware_data(self) -> dict[Any, Any]:
        """Middleware data."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dialog_data(self) -> dict[Any, Any]:
        """Dialog data for current context."""
        raise NotImplementedError

    @property
    @abstractmethod
    def start_data(self) -> Data:
        """Start data for current context."""
        raise NotImplementedError

    @property
    @abstractmethod
    def show_mode(self) -> ShowMode:
        """Get current show mode, used for next show action."""
        raise NotImplementedError

    @show_mode.setter
    @abstractmethod
    def show_mode(self, show_mode: ShowMode) -> None:
        """Set current show mode, used for next show action."""
        raise NotImplementedError

    @abstractmethod
    def is_preview(self) -> bool:
        """Check if this manager is used only to generate dialog preview."""
        raise NotImplementedError

    @abstractmethod
    async def show(self, show_mode: ShowMode | None = None) -> None:
        """Show current state to the user."""
        raise NotImplementedError

    @abstractmethod
    async def answer_callback(self) -> None:
        """Answer to a callback query."""
        raise NotImplementedError

    @abstractmethod
    def current_context(self) -> Context:
        """
        Get current dialog context.

        :raise NoContextError if there is no open dialog
        """
        raise NotImplementedError

    @abstractmethod
    def has_context(self) -> bool:
        """Check if there is current context."""
        raise NotImplementedError

    @abstractmethod
    def current_stack(self) -> Stack:
        """Get current dialog stack."""
        raise NotImplementedError

    @abstractmethod
    async def next(self, show_mode: ShowMode | None = None) -> None:
        """Switch to the next state within current dialog."""
        raise NotImplementedError

    @abstractmethod
    async def back(self, show_mode: ShowMode | None = None) -> None:
        """Switch to the previous state within current dialog."""
        raise NotImplementedError

    @abstractmethod
    def find(self, widget_id: str) -> Optional["Widget"]:
        """
        Find a widget in current dialog by its id.

        Returns managed adapter for found widget,
        which does not require to pass manager and has only subset of methods.
        """
        raise NotImplementedError

    @abstractmethod
    async def reset_stack(self, remove_keyboard: bool = True) -> None:
        """
        Reset current stack.

        No callbacks are called, contexts are removed from storage.
        """
        raise NotImplementedError

    @abstractmethod
    async def load_data(self) -> dict[Any, Any]:
        """Load data for current state."""
        raise NotImplementedError

    @abstractmethod
    async def close_manager(self) -> None:
        """Release all resources and disable usage of many methods."""
        raise NotImplementedError
