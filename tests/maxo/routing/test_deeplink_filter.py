from datetime import UTC, datetime

from maxo import Ctx
from maxo.routing.filters import DeeplinkFilter
from maxo.routing.updates import BotStarted
from maxo.types import User
from maxo.utils.payload import encode_payload


def bot_started(payload: str | None) -> BotStarted:
    return BotStarted(
        chat_id=1,
        user=User(
            first_name="42",
            is_bot=False,
            last_activity_time=datetime.fromtimestamp(1234567890, tz=UTC),
            user_id=42,
        ),
        payload=payload,
        timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
    )


async def test_deeplink_is_none() -> None:
    filter = DeeplinkFilter()
    event = bot_started(payload=None)

    ctx = Ctx({})
    assert await filter(event, ctx) is False
    assert ctx == {}


async def test_deeplink_is_empty() -> None:
    filter = DeeplinkFilter()
    event = bot_started(payload="")

    ctx = Ctx({})
    assert await filter(event, ctx) is False
    assert ctx == {}


async def test_deeplink_is_filled() -> None:
    filter = DeeplinkFilter()
    event = bot_started(payload="helloworld")

    ctx = Ctx({})
    assert await filter(event, ctx) is True

    assert len(ctx) == 3
    assert ctx["payload"] == ctx["deeplink"] == ctx["args"] == "helloworld"


async def test_deeplink_is_filled_and_encoded() -> None:
    filter = DeeplinkFilter(deep_link_encoded=True)
    event = bot_started(payload=encode_payload("helloworld"))

    ctx = Ctx({})
    assert await filter(event, ctx) is True

    assert len(ctx) == 3
    assert ctx["payload"] == ctx["deeplink"] == ctx["args"] == "helloworld"


async def test_deeplink_is_filled_and_bad_encoded() -> None:
    filter = DeeplinkFilter(deep_link_encoded=True)
    event = bot_started(payload="amongus_")

    ctx = Ctx({})
    assert await filter(event, ctx) is False
    assert ctx == {}
