# ruff: noqa: E402

import warnings

warnings.warn(
    "Фасады были перенесены из `maxo.utils.facades` "
    "в `maxo.routing.facades` и `maxo.routing.mixins`. "
    "Пожалуйста, обновите импорты "
    "на `from maxo.routing.facades import ...` "
    "или `from maxo.routing.mixins import ...`",
    DeprecationWarning,
    stacklevel=2,
)

from maxo.routing.facades.base import BaseUpdateFacade
from maxo.routing.facades.bot_added_to_chat import BotAddedToChatFacade
from maxo.routing.facades.bot_removed_from_chat import BotRemovedFromChatFacade
from maxo.routing.facades.bot_started import BotStartedFacade
from maxo.routing.facades.bot_stopped import BotStoppedFacade
from maxo.routing.facades.chat_title_changed import ChatTitleChangedFacade
from maxo.routing.facades.dialog_cleared import DialogClearedFacade
from maxo.routing.facades.dialog_muted import DialogMutedFacade
from maxo.routing.facades.dialog_removed import DialogRemovedFacade
from maxo.routing.facades.dialog_unmuted import DialogUnmutedFacade
from maxo.routing.facades.error import ErrorEventFacade
from maxo.routing.facades.message_callback import MessageCallbackFacade
from maxo.routing.facades.message_created import MessageCreatedFacade
from maxo.routing.facades.message_edited import MessageEditedFacade
from maxo.routing.facades.message_removed import MessageRemovedFacade
from maxo.routing.facades.user_added_to_chat import UserAddedToChatFacade
from maxo.routing.facades.user_removed_from_chat import UserRemovedFromChatFacade
from maxo.routing.mixins import (
    AttachmentsFacade,
    BaseMethodsFacade,
    BotMethodsFacade,
    ChatMethodsFacade,
    MessageMethodsFacade,
    SubscriptionMethodsFacade,
)
from maxo.routing.mixins.callback import CallbackMethodsFacade

__all__ = (
    "AttachmentsFacade",
    "BaseMethodsFacade",
    "BaseUpdateFacade",
    "BotAddedToChatFacade",
    "BotMethodsFacade",
    "BotRemovedFromChatFacade",
    "BotStartedFacade",
    "BotStoppedFacade",
    "CallbackMethodsFacade",
    "ChatMethodsFacade",
    "ChatTitleChangedFacade",
    "DialogClearedFacade",
    "DialogMutedFacade",
    "DialogRemovedFacade",
    "DialogUnmutedFacade",
    "ErrorEventFacade",
    "MessageCallbackFacade",
    "MessageCreatedFacade",
    "MessageEditedFacade",
    "MessageMethodsFacade",
    "MessageRemovedFacade",
    "SubscriptionMethodsFacade",
    "UserAddedToChatFacade",
    "UserRemovedFromChatFacade",
)
