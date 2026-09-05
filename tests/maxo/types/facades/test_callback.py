from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.omit import Omitted
from maxo.types.callback import Callback
from maxo.types.facades.callback import CallbackMethodsFacade
from maxo.types.new_message_body import NewMessageBody
from maxo.types.simple_query_result import SimpleQueryResult
from maxo.types.user import User
from tests.constants import NOW


class MockCallbackFacade(CallbackMethodsFacade):
    def __init__(self, bot: MagicMock) -> None:
        self._bot = bot

    @property
    def callback(self) -> Callback:
        return Callback(
            callback_id="cb",
            timestamp=NOW,
            user=User(user_id=1, first_name="Alice", is_bot=False),
        )


@pytest.fixture
def mock_bot() -> MagicMock:
    bot = MagicMock()
    bot.answer_on_callback = AsyncMock(return_value=SimpleQueryResult(success=True))
    return bot


@pytest.fixture
def facade(mock_bot: MagicMock) -> MockCallbackFacade:
    return MockCallbackFacade(mock_bot)


async def test_callback_answer_defaults(
    facade: MockCallbackFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.callback_answer()

    mock_bot.answer_on_callback.assert_awaited_once_with(
        callback_id="cb",
        notification=Omitted(),
        message=None,
        disable_link_preview=Omitted(),
    )


async def test_callback_answer_forwards_all_params(
    facade: MockCallbackFacade,
    mock_bot: MagicMock,
) -> None:
    message = NewMessageBody(text="edited")

    await facade.callback_answer(
        notification="Готово",
        message=message,
        disable_link_preview=True,
    )

    mock_bot.answer_on_callback.assert_awaited_once_with(
        callback_id="cb",
        notification="Готово",
        message=message,
        disable_link_preview=True,
    )


async def test_callback_answer_uses_text_alias(
    facade: MockCallbackFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.callback_answer(text="Готово", disable_link_preview=False)

    mock_bot.answer_on_callback.assert_awaited_once_with(
        callback_id="cb",
        notification="Готово",
        message=None,
        disable_link_preview=False,
    )


async def test_callback_answer_prefers_notification_over_text(
    facade: MockCallbackFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.callback_answer(notification="Первое", text="Второе")

    assert mock_bot.answer_on_callback.await_args.kwargs["notification"] == "Первое"


async def test_answer_alias_forwards_disable_link_preview(
    facade: MockCallbackFacade,
    mock_bot: MagicMock,
) -> None:
    await facade.answer(notification="Готово", disable_link_preview=True)

    mock_bot.answer_on_callback.assert_awaited_once_with(
        callback_id="cb",
        notification="Готово",
        message=None,
        disable_link_preview=True,
    )
