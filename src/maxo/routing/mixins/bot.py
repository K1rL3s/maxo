from maxo.omit import Omittable, Omitted
from maxo.routing.mixins.base import BaseMethodsFacade
from maxo.types.bot_command import BotCommand
from maxo.types.bot_info import BotInfo
from maxo.types.photo_attachment_request_payload import PhotoAttachmentRequestPayload


class BotMethodsFacade(BaseMethodsFacade):
    __slots__ = ()

    async def get_my_info(self) -> BotInfo:
        return await self.bot.get_my_info()

    async def edit_bot_info(
        self,
        first_name: Omittable[str | None] = Omitted(),
        last_name: Omittable[str | None] = Omitted(),
        description: Omittable[str | None] = Omitted(),
        commands: Omittable[list[BotCommand] | None] = Omitted(),
        photo: Omittable[PhotoAttachmentRequestPayload | None] = Omitted(),
    ) -> BotInfo:
        return await self.bot.edit_bot_info(
            first_name=first_name,
            last_name=last_name,
            description=description,
            commands=commands,
            photo=photo,
        )
