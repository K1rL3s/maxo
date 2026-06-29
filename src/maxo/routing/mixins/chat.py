from abc import abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import TYPE_CHECKING

from maxo.enums import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.routing.mixins.attachments import AttachmentsFacade, MediaInput
from maxo.types.attachments import AttachmentsRequests
from maxo.types.buttons import InlineButtons
from maxo.types.chat_members_list import ChatMembersList
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult

if TYPE_CHECKING:
    from maxo.types.chat import Chat
    from maxo.types.message import Message
    from maxo.types.message_list import MessageList


class ChatMethodsFacade(AttachmentsFacade):
    __slots__ = ()

    @property
    @abstractmethod
    def chat_id(self) -> int:
        raise NotImplementedError

    async def send_message(
        self,
        text: str | None = None,
        link: NewMessageLink | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        disable_link_preview: Omittable[bool] = Omitted(),
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        media: Sequence[MediaInput] | None = None,
        attachments: Sequence[AttachmentsRequests] | None = None,
    ) -> "Message":
        prepared_attachments = await self.build_attachments(
            base=attachments or [],
            keyboard=keyboard,
            files=media,
        )

        result = await self.bot.send_message(
            chat_id=self.chat_id,
            text=text,
            attachments=prepared_attachments,
            link=link,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    async def get_chat(self) -> "Chat":
        return await self.bot.get_chat(chat_id=self.chat_id)

    async def get_members(
        self,
        count: Omittable[int] = Omitted(),
        marker: Omittable[int] = Omitted(),
        user_ids: Omittable[list[int] | None] = Omitted(),
    ) -> ChatMembersList:
        return await self.bot.get_members(
            chat_id=self.chat_id,
            count=count,
            marker=marker,
            user_ids=user_ids,
        )

    async def leave_chat(self) -> SimpleQueryResult:
        return await self.bot.leave_chat(chat_id=self.chat_id)

    async def get_messages(
        self,
        count: Omittable[int] = Omitted(),
        from_: Omittable[datetime] = Omitted(),
        message_ids: Omittable[list[str] | None] = Omitted(),
        to: Omittable[datetime] = Omitted(),
    ) -> "MessageList":
        return await self.bot.get_messages(
            chat_id=self.chat_id,
            count=count,
            from_=from_,
            message_ids=message_ids,
            to=to,
        )
