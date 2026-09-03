from unihttp.clients.base import BaseAsyncClient

from maxo.bot import UploadConfig
from maxo.bot.defaults import BotDefaults
from maxo.types import MaxoType


class BotConfig(MaxoType):
    client: BaseAsyncClient

    defaults: BotDefaults | None = None
    upload_config: UploadConfig | None = None
    warming_up: bool = True
