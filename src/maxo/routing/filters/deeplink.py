from maxo import Ctx
from maxo.omit import is_not_defined
from maxo.routing.filters.base import BaseFilter
from maxo.routing.updates.bot_started import BotStarted
from maxo.utils.payload import decode_payload


class DeeplinkFilter(BaseFilter[BotStarted]):
    def __init__(self, deep_link_encoded: bool = False) -> None:
        self.deep_link_encoded = deep_link_encoded

    async def __call__(self, event: BotStarted, ctx: Ctx) -> bool:
        payload = event.payload
        if is_not_defined(payload) or not payload:
            return False

        try:
            deeplink = self.validate_deeplink(payload)
        except ValueError:
            return False

        # ctx["args"] для работы `F.args.startswith(...)`,
        # как при фильтрации диплинков из тг с CommandStart
        ctx["payload"] = ctx["deeplink"] = ctx["args"] = deeplink
        return True

    def validate_deeplink(self, payload: str) -> str:
        if self.deep_link_encoded:
            try:
                payload = decode_payload(payload)
            except UnicodeDecodeError as e:
                raise ValueError(f"Failed to decode Base64: {e}") from e
        return payload
