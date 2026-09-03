from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.omit import Omitted
from maxo.types.facades.subscription import SubscriptionMethodsFacade
from maxo.types.get_subscriptions_result import GetSubscriptionsResult
from maxo.types.simple_query_result import SimpleQueryResult


class MockSubscriptionFacade(SubscriptionMethodsFacade):
    def __init__(self, bot: MagicMock) -> None:
        self._bot = bot


@pytest.fixture
def mock_bot() -> MagicMock:
    bot = MagicMock()
    bot.get_subscriptions = AsyncMock(
        return_value=GetSubscriptionsResult(subscriptions=[]),
    )
    bot.get_updates = AsyncMock(return_value=MagicMock())
    bot.subscribe = AsyncMock(return_value=SimpleQueryResult(success=True))
    bot.unsubscribe = AsyncMock(return_value=SimpleQueryResult(success=True))
    return bot


@pytest.fixture
def facade(mock_bot: MagicMock) -> MockSubscriptionFacade:
    return MockSubscriptionFacade(mock_bot)


async def test_get_subscriptions(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    result = await facade.get_subscriptions()

    mock_bot.get_subscriptions.assert_called_once_with()
    assert isinstance(result, GetSubscriptionsResult)


async def test_get_updates_no_params(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_updates()

    mock_bot.get_updates.assert_called_once_with(
        limit=Omitted(),
        marker=Omitted(),
        timeout=Omitted(),
        types=Omitted(),
    )


async def test_get_updates_with_limit(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_updates(limit=100)

    mock_bot.get_updates.assert_called_once_with(
        limit=100,
        marker=Omitted(),
        timeout=Omitted(),
        types=Omitted(),
    )


async def test_get_updates_with_all_params(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_updates(
        limit=50,
        marker=12345,
        timeout=30,
        types=["message_created", "message_callback"],
    )

    mock_bot.get_updates.assert_called_once_with(
        limit=50,
        marker=12345,
        timeout=30,
        types=["message_created", "message_callback"],
    )


async def test_get_updates_with_none_marker(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.get_updates(marker=None)

    mock_bot.get_updates.assert_called_once_with(
        limit=Omitted(),
        marker=None,
        timeout=Omitted(),
        types=Omitted(),
    )


async def test_subscribe_minimal(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    result = await facade.subscribe(url="https://example.com/webhook")

    mock_bot.subscribe.assert_called_once_with(
        url="https://example.com/webhook",
        secret=Omitted(),
        update_types=Omitted(),
    )
    assert result.success is True


async def test_subscribe_with_secret(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.subscribe(
        url="https://example.com/webhook",
        secret="my_secret",  # noqa: S106
    )

    mock_bot.subscribe.assert_called_once_with(
        url="https://example.com/webhook",
        secret="my_secret",  # noqa: S106
        update_types=Omitted(),
    )


async def test_subscribe_with_all_params(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.subscribe(
        url="https://example.com/webhook",
        secret="my_secret",  # noqa: S106
        update_types=["message_created", "bot_started"],
    )

    mock_bot.subscribe.assert_called_once_with(
        url="https://example.com/webhook",
        secret="my_secret",  # noqa: S106
        update_types=["message_created", "bot_started"],
    )


async def test_unsubscribe(
    facade: MockSubscriptionFacade,
    mock_bot: MagicMock,
) -> None:
    result = await facade.unsubscribe(url="https://example.com/webhook")

    mock_bot.unsubscribe.assert_called_once_with(url="https://example.com/webhook")
    assert result.success is True
