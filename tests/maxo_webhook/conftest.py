import pytest

from maxo import Bot
from tests.maxo_webhook.fixtures.web_request import DummyRequest, DummyWebRequest
from tests.maxo_webhook.fixtures.webhook_engine import CapturingAdapter, DummyDispatcher


@pytest.fixture
def bot_id() -> int:
    return 42


@pytest.fixture
def bot_token(bot_id: int) -> str:
    return f"{bot_id}:TEST"


@pytest.fixture
def bot(bot_token: str) -> Bot:
    return Bot(bot_token, warming_up=False)


@pytest.fixture
def adapter() -> CapturingAdapter:
    return CapturingAdapter()


@pytest.fixture
def update_request() -> DummyWebRequest:
    return DummyWebRequest(
        DummyRequest(
            json_data={
                "update_type": "message_created",
                "timestamp": 1234567890,
                "message": {
                    "body": {"seq": 1, "mid": "msg-1", "text": "hello"},
                    "recipient": {"chat_id": 1, "chat_type": "dialog"},
                    "timestamp": 1234567890,
                },
            },
        ),
    )


@pytest.fixture
def dispatcher() -> DummyDispatcher:
    return DummyDispatcher()
