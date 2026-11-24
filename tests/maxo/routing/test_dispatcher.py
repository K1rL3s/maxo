import logging

import pytest

from maxo.enums import ChatType
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.sentinels import UNHANDLED
from maxo.routing.signals import BeforeStartup, MaxoUpdate
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW
from tests.factories import make_bot


@pytest.fixture
def update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text="/start"),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
    )


async def handler(update: MessageCreated) -> str:
    return "OK"


class TestFeedMaxUpdateLogging:
    """#289: результат хендлера не должен попадать в лог на уровне INFO."""

    async def test_info_log_omits_handler_result(
        self,
        update: MessageCreated,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        dp = Dispatcher(disable_fsm=True)
        dp.message_created.handler(handler)
        await dp.feed_signal(BeforeStartup())

        with caplog.at_level(logging.INFO, logger="maxo.dispatcher"):
            result = await dp.feed_max_update(MaxoUpdate(update=update), make_bot())

        assert result == "OK"
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_records) == 1
        message = info_records[0].getMessage()
        assert "Handled update" in message
        assert "OK" not in message

    async def test_debug_log_includes_handler_result(
        self,
        update: MessageCreated,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        dp = Dispatcher(disable_fsm=True)
        dp.message_created.handler(handler)
        await dp.feed_signal(BeforeStartup())

        with caplog.at_level(logging.DEBUG, logger="maxo.dispatcher"):
            result = await dp.feed_max_update(MaxoUpdate(update=update), make_bot())

        assert result == "OK"
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 1
        assert "OK" in debug_records[0].getMessage()

    async def test_not_handled_update_logs_without_result(
        self,
        update: MessageCreated,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        dp = Dispatcher(disable_fsm=True)
        await dp.feed_signal(BeforeStartup())

        with caplog.at_level(logging.DEBUG, logger="maxo.dispatcher"):
            result = await dp.feed_max_update(MaxoUpdate(update=update), make_bot())

        assert result is UNHANDLED
        info_records = [r for r in caplog.records if r.levelno == logging.INFO]
        assert len(info_records) == 1
        assert "Not handled update" in info_records[0].getMessage()
        debug_records = [r for r in caplog.records if r.levelno == logging.DEBUG]
        assert len(debug_records) == 1
        assert repr(UNHANDLED) in debug_records[0].getMessage()
