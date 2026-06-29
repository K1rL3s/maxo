from asyncio import Future
from enum import Enum
from typing import TYPE_CHECKING, Any

from maxo import Bot
from maxo.fsm import State
from maxo.routing.updates import BaseUpdate
from maxo.types import Recipient, User

from .access import AccessSettings
from .modes import ShowMode, StartMode

if TYPE_CHECKING:
    from maxo.dialogs.api.protocols.manager import DialogManager


DIALOG_EVENT_NAME = "aiogd_update"


class DialogAction(Enum):
    DONE = "DONE"
    START = "START"
    UPDATE = "UPDATE"
    SWITCH = "SWITCH"
    FG = "FG"


class DialogUpdateEvent(BaseUpdate):
    user: User
    recipient: Recipient
    action: DialogAction
    data: Any
    intent_id: str | None
    stack_id: str | None
    show_mode: ShowMode | None = None
    bot: Bot

    # Для частичной совместимости с `MaxUpdate`
    @property
    def event_type(self) -> str:
        return DIALOG_EVENT_NAME


class DialogStartEvent(DialogUpdateEvent):
    new_state: State
    mode: StartMode
    access_settings: AccessSettings | None = None


class DialogSwitchEvent(DialogUpdateEvent):
    new_state: State


class DialogFgEvent(DialogUpdateEvent):
    entered: Future["DialogManager"]
    exited: Future[None]
