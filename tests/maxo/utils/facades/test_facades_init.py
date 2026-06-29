import importlib

import pytest

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


def test_deprecation_warning():
    with pytest.warns(
        DeprecationWarning,
        match="Фасады были перенесены из `maxo.utils.facades`",
    ):
        import maxo.utils.facades  # noqa: PLC0415

    importlib.reload(maxo.utils.facades)


def test_all_facades_are_exported():
    import maxo.utils.facades  # noqa: PLC0415

    assert hasattr(maxo.utils.facades, "AttachmentsFacade")
    assert maxo.utils.facades.AttachmentsFacade is AttachmentsFacade

    assert hasattr(maxo.utils.facades, "BaseMethodsFacade")
    assert maxo.utils.facades.BaseMethodsFacade is BaseMethodsFacade

    assert hasattr(maxo.utils.facades, "BaseUpdateFacade")
    assert maxo.utils.facades.BaseUpdateFacade is BaseUpdateFacade

    assert hasattr(maxo.utils.facades, "BotAddedToChatFacade")
    assert maxo.utils.facades.BotAddedToChatFacade is BotAddedToChatFacade

    assert hasattr(maxo.utils.facades, "BotMethodsFacade")
    assert maxo.utils.facades.BotMethodsFacade is BotMethodsFacade

    assert hasattr(maxo.utils.facades, "BotRemovedFromChatFacade")
    assert maxo.utils.facades.BotRemovedFromChatFacade is BotRemovedFromChatFacade

    assert hasattr(maxo.utils.facades, "BotStartedFacade")
    assert maxo.utils.facades.BotStartedFacade is BotStartedFacade

    assert hasattr(maxo.utils.facades, "BotStoppedFacade")
    assert maxo.utils.facades.BotStoppedFacade is BotStoppedFacade

    assert hasattr(maxo.utils.facades, "CallbackMethodsFacade")
    assert maxo.utils.facades.CallbackMethodsFacade is CallbackMethodsFacade

    assert hasattr(maxo.utils.facades, "ChatMethodsFacade")
    assert maxo.utils.facades.ChatMethodsFacade is ChatMethodsFacade

    assert hasattr(maxo.utils.facades, "ChatTitleChangedFacade")
    assert maxo.utils.facades.ChatTitleChangedFacade is ChatTitleChangedFacade

    assert hasattr(maxo.utils.facades, "DialogClearedFacade")
    assert maxo.utils.facades.DialogClearedFacade is DialogClearedFacade

    assert hasattr(maxo.utils.facades, "DialogMutedFacade")
    assert maxo.utils.facades.DialogMutedFacade is DialogMutedFacade

    assert hasattr(maxo.utils.facades, "DialogRemovedFacade")
    assert maxo.utils.facades.DialogRemovedFacade is DialogRemovedFacade

    assert hasattr(maxo.utils.facades, "DialogUnmutedFacade")
    assert maxo.utils.facades.DialogUnmutedFacade is DialogUnmutedFacade

    assert hasattr(maxo.utils.facades, "ErrorEventFacade")
    assert maxo.utils.facades.ErrorEventFacade is ErrorEventFacade

    assert hasattr(maxo.utils.facades, "MessageCallbackFacade")
    assert maxo.utils.facades.MessageCallbackFacade is MessageCallbackFacade

    assert hasattr(maxo.utils.facades, "MessageCreatedFacade")
    assert maxo.utils.facades.MessageCreatedFacade is MessageCreatedFacade

    assert hasattr(maxo.utils.facades, "MessageEditedFacade")
    assert maxo.utils.facades.MessageEditedFacade is MessageEditedFacade

    assert hasattr(maxo.utils.facades, "MessageMethodsFacade")
    assert maxo.utils.facades.MessageMethodsFacade is MessageMethodsFacade

    assert hasattr(maxo.utils.facades, "MessageRemovedFacade")
    assert maxo.utils.facades.MessageRemovedFacade is MessageRemovedFacade

    assert hasattr(maxo.utils.facades, "SubscriptionMethodsFacade")
    assert maxo.utils.facades.SubscriptionMethodsFacade is SubscriptionMethodsFacade

    assert hasattr(maxo.utils.facades, "UserAddedToChatFacade")
    assert maxo.utils.facades.UserAddedToChatFacade is UserAddedToChatFacade

    assert hasattr(maxo.utils.facades, "UserRemovedFromChatFacade")
    assert maxo.utils.facades.UserRemovedFromChatFacade is UserRemovedFromChatFacade
