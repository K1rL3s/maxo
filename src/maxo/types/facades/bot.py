from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import deprecated

from maxo.omit import Omittable, Omitted

if TYPE_CHECKING:
    from maxo.bot.bot import Bot
    from maxo.types.bot_command import BotCommand
    from maxo.types.bot_info import BotInfo
    from maxo.types.photo_attachment_request_payload import (
        PhotoAttachmentRequestPayload,
    )


class BotMethodsFacade:
    """
    Root of the facades: stateless mixins with API shortcuts.

    A facade declares what it needs from its host (`bot`, `chat_id`, `message`,
    `callback`) as properties under `TYPE_CHECKING` only. At runtime such a
    property would become the default of the host's dataclass field. A plain
    annotation won't do either: it declares a writable attribute, which
    computed properties like `Message.message` can't override.
    """

    __slots__ = ()

    if TYPE_CHECKING:

        @property
        def bot(self) -> Bot: ...

    async def get_my_info(self) -> BotInfo:
        return await self.bot.get_my_info()

    @deprecated("PATCH /me нет в API MAX, команды задаёт EditMyCommands")
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
