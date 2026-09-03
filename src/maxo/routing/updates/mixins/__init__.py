# ruff: noqa: E402

import warnings

warnings.warn(
    "Миксины были перенесены из `maxo.routing.updates.mixins` в `maxo.types.facades`. "
    "Пожалуйста, обновите импорты "
    "на `from maxo.types.facades import ...` ",
    DeprecationWarning,
    stacklevel=2,
)

from maxo.types.facades.attachments import AttachmentsFacade, MediaInput
from maxo.types.facades.base import BaseMethodsFacade
from maxo.types.facades.bot import BotMethodsFacade
from maxo.types.facades.callback import CallbackMethodsFacade
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.facades.message import MessageMethodsFacade
from maxo.types.facades.subscription import SubscriptionMethodsFacade

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
