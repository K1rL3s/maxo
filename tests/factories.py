from typing import Any

from maxo import Bot, Ctx
from maxo.routing.flags import HANDLER_KEY
from maxo.routing.handlers.update import UpdateHandler
from maxo.types import BotInfo
from maxo.types.base import BaseUpdate
from tests.constants import BOT_ID, NOW, TOKEN


def make_bot(token: str = TOKEN, **kwargs: Any) -> Bot:
    return Bot(token=token, warming_up=False, **kwargs)


def make_bot_info(
    user_id: int = BOT_ID,
    username: str = "testbot",
    first_name: str = "Test",
) -> BotInfo:
    return BotInfo(
        user_id=user_id,
        is_bot=True,
        first_name=first_name,
        username=username,
        last_activity_time=NOW,
    )


async def _stub_handler(update: BaseUpdate) -> None:
    pass


def make_flagged_handler(**flags: Any) -> UpdateHandler[Any, None]:
    return UpdateHandler(_stub_handler, flags=flags)


def make_flagged_ctx(**flags: Any) -> Ctx:
    return Ctx({HANDLER_KEY: make_flagged_handler(**flags)})
