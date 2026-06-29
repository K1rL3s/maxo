# ruff: noqa: PLC0415
import importlib

import pytest

from maxo.routing.mixins.attachments import AttachmentsFacade, MediaInput
from maxo.routing.mixins.base import BaseMethodsFacade
from maxo.routing.mixins.bot import BotMethodsFacade
from maxo.routing.mixins.callback import CallbackMethodsFacade
from maxo.routing.mixins.chat import ChatMethodsFacade
from maxo.routing.mixins.message import MessageMethodsFacade
from maxo.routing.mixins.subscription import SubscriptionMethodsFacade


def test_deprecation_warning():
    with pytest.warns(
        DeprecationWarning,
        match="Миксины были перенесены из `maxo.routing.updates.mixins`",
    ):
        import maxo.routing.updates.mixins

    importlib.reload(maxo.routing.updates.mixins)


def test_all_mixins_are_exported():
    import maxo.routing.updates.mixins

    assert hasattr(maxo.routing.updates.mixins, "AttachmentsFacade")
    assert maxo.routing.updates.mixins.AttachmentsFacade is AttachmentsFacade

    assert hasattr(maxo.routing.updates.mixins, "BaseMethodsFacade")
    assert maxo.routing.updates.mixins.BaseMethodsFacade is BaseMethodsFacade

    assert hasattr(maxo.routing.updates.mixins, "BotMethodsFacade")
    assert maxo.routing.updates.mixins.BotMethodsFacade is BotMethodsFacade

    assert hasattr(maxo.routing.updates.mixins, "CallbackMethodsFacade")
    assert maxo.routing.updates.mixins.CallbackMethodsFacade is CallbackMethodsFacade

    assert hasattr(maxo.routing.updates.mixins, "ChatMethodsFacade")
    assert maxo.routing.updates.mixins.ChatMethodsFacade is ChatMethodsFacade

    assert hasattr(maxo.routing.updates.mixins, "MediaInput")
    assert maxo.routing.updates.mixins.MediaInput is MediaInput

    assert hasattr(maxo.routing.updates.mixins, "MessageMethodsFacade")
    assert maxo.routing.updates.mixins.MessageMethodsFacade is MessageMethodsFacade

    assert hasattr(maxo.routing.updates.mixins, "SubscriptionMethodsFacade")
    assert (
        maxo.routing.updates.mixins.SubscriptionMethodsFacade
        is SubscriptionMethodsFacade
    )
