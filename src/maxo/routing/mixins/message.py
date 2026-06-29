from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from maxo.enums import MessageLinkType, TextFormat
from maxo.omit import Omittable, Omitted, is_defined
from maxo.routing.mixins.attachments import MediaInput
from maxo.routing.mixins.chat import ChatMethodsFacade
from maxo.types.attachments import AttachmentsRequests
from maxo.types.buttons import InlineButtons
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult
from maxo.utils.helpers.calculating import calculate_chat_id_and_user_id

if TYPE_CHECKING:
    from maxo.types.message import Message


class MessageMethodsFacade(ChatMethodsFacade):
    __slots__ = ()

    @property
    @abstractmethod
    def message(self) -> "Message":
        raise NotImplementedError

    @property
    def chat_id(self) -> int:
        return self.message.recipient.unsafe_chat_id

    async def delete_message(self) -> SimpleQueryResult:
        message_id = self.message.body.mid
        return await self.bot.delete_message(message_id=message_id)

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
        recipient = self.message.recipient
        sender = self.message.sender
        chat_id, user_id = calculate_chat_id_and_user_id(
            chat_id=recipient.chat_id,
            user_id=sender.user_id if is_defined(sender) else None,
            chat_type=recipient.chat_type,
        )

        attachments = await self.build_attachments(
            base=attachments or [],
            keyboard=keyboard,
            files=media,
        )

        result = await self.bot.send_message(
            chat_id=chat_id,
            user_id=user_id,
            text=text,
            attachments=attachments,
            link=link,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    answer = send_message

    async def reply(
        self,
        text: str | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        disable_link_preview: Omittable[bool] = Omitted(),
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        media: Sequence[MediaInput] | None = None,
        attachments: Sequence[AttachmentsRequests] | None = None,
    ) -> "Message":
        link = self._make_new_message_link(type=MessageLinkType.REPLY)
        return await self.send_message(
            text=text,
            link=link,
            notify=notify,
            format=format,
            disable_link_preview=disable_link_preview,
            keyboard=keyboard,
            media=media,
            attachments=attachments,
        )

    async def answer_text(
        self,
        text: str,
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> "Message":
        return await self.send_message(
            text=text,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
        )

    async def reply_text(
        self,
        text: str,
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> "Message":
        return await self.send_message(
            text=text,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
            link=self._make_new_message_link(MessageLinkType.REPLY),
        )

    async def send_media(
        self,
        media: MediaInput | Sequence[MediaInput],
        text: str | None = None,
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        notify: Omittable[bool] = True,
        format: Omittable[TextFormat | None] = Omitted(),
        link: NewMessageLink | None = None,
        disable_link_preview: Omittable[bool] = Omitted(),
    ) -> "Message":
        if not isinstance(media, Sequence):
            media = (media,)

        return await self.send_message(
            text=text,
            media=media,
            notify=notify,
            format=format,
            keyboard=keyboard,
            disable_link_preview=disable_link_preview,
            link=link,
        )

    async def edit_message(
        self,
        text: str | None = None,
        keyboard: Sequence[Sequence[InlineButtons]] | None = None,
        media: Sequence[MediaInput] | None = None,
        link: NewMessageLink | None = None,
        notify: bool = True,
        format: Omittable[TextFormat | None] = Omitted(),
        attachments: Sequence[AttachmentsRequests] | None = None,
    ) -> SimpleQueryResult:
        message_id = self.message.body.mid

        if text is None:
            text = self.message.body.text

        if attachments is None and keyboard is None and media is None:
            # Для случая, когда не надо редачить аттачменты
            prepared_attachments = None
        else:
            prepared_attachments = await self.build_attachments(
                base=attachments or [],
                keyboard=keyboard,
                files=media,
            )

        return await self.bot.edit_message(
            message_id=message_id,
            text=text,
            attachments=prepared_attachments,
            link=link,
            notify=notify,
            format=format,
        )

    def _make_new_message_link(self, type: MessageLinkType) -> NewMessageLink:
        return NewMessageLink(
            type=type,
            mid=self.message.body.mid,
        )

    async def get_message_by_id(self, message_id: str) -> "Message":
        return await self.bot.get_message_by_id(message_id=message_id)
