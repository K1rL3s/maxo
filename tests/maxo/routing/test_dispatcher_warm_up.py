from unittest.mock import Mock

import pytest

from maxo import Dispatcher
from maxo.routing.signals import BeforeStartup


@pytest.mark.asyncio
async def test_before_startup_warms_up(monkeypatch: pytest.MonkeyPatch) -> None:
    warm_up = Mock()
    monkeypatch.setattr("maxo.routing.dispatcher.warm_up", warm_up)

    await Dispatcher().feed_signal(BeforeStartup())

    warm_up.assert_called_once_with()
