# ruff: noqa: E402

import warnings

warnings.warn(
    "Миксины были перенесены из `maxo.routing.updates.mixins` в `maxo.routing.mixins`. "
    "Пожалуйста, обновите импорты "
    "на `from maxo.routing.mixins import ...` ",
    DeprecationWarning,
    stacklevel=2,
)

from maxo.routing.mixins.attachments import AttachmentsFacade, MediaInput
from maxo.routing.mixins.base import BaseMethodsFacade
from maxo.routing.mixins.bot import BotMethodsFacade
from maxo.routing.mixins.callback import CallbackMethodsFacade
from maxo.routing.mixins.chat import ChatMethodsFacade
from maxo.routing.mixins.message import MessageMethodsFacade
from maxo.routing.mixins.subscription import SubscriptionMethodsFacade

__all__ = (
    "AttachmentsFacade",
    "BaseMethodsFacade",
    "BotMethodsFacade",
    "CallbackMethodsFacade",
    "ChatMethodsFacade",
    "MediaInput",
    "MessageMethodsFacade",
    "SubscriptionMethodsFacade",
)
