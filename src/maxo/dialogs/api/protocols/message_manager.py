from abc import abstractmethod
from typing import Protocol

from maxo import Bot
from maxo.dialogs import ShowMode
from maxo.dialogs.api.entities import NewMessage, OldMessage
from maxo.dialogs.api.exceptions import DialogsError
from maxo.types import Callback


class MessageNotModified(DialogsError):
    pass


class MessageManagerProtocol(Protocol):
    @abstractmethod
    async def remove_kbd(
        self,
        bot: Bot,
        show_mode: ShowMode,
        old_message: OldMessage | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def show_message(
        self,
        bot: Bot,
        new_message: NewMessage,
        old_message: OldMessage | None,
    ) -> OldMessage:
        raise NotImplementedError

    @abstractmethod
    async def answer_callback(
        self,
        bot: Bot,
        callback: Callback,
    ) -> None:
        raise NotImplementedError
