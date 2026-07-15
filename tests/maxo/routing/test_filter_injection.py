from typing import Any

from maxo import Bot, Ctx
from maxo.enums import ChatType
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW
from tests.factories import make_bot


class BotFilter(BaseFilter[Any]):
    def __init__(self) -> None:
        self.bot: Bot | None = None

    async def __call__(self, update: Any, ctx: Ctx, bot: Bot) -> bool:
        self.bot = bot
        return True


def make_update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text="text"),
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


async def test_filter_receives_dependency_from_context() -> None:
    dp = Dispatcher()
    filter_ = BotFilter()
    bot = make_bot()

    @dp.message_created(filter_)
    async def handler(update: MessageCreated) -> str:
        return "ok"

    assert await dp.feed_update(make_update(), bot) == "ok"
    assert filter_.bot is bot
