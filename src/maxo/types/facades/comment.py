from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

from maxo import loggers
from maxo.enums import MessageLinkType, TextFormat
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachments import AttachmentsRequests
from maxo.types.buttons import InlineButtons
from maxo.types.facades.attachments import MediaInput
from maxo.types.facades.message import MessageMethodsFacade
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult

if TYPE_CHECKING:
    from maxo.types.comment_message import CommentMessage


class CommentMethodsFacade(MessageMethodsFacade):
    __slots__ = ()

    if TYPE_CHECKING:

        @property
        @abstractmethod
        def message(self) -> "CommentMessage | None":
            raise NotImplementedError

    else:
        message: "CommentMessage | None"

    async def delete_message(self) -> SimpleQueryResult:
        comment = self.unsafe_message
        return await self.bot.delete_comment(
            message_id=comment.recipient.unsafe_post_id,
            comment_id=comment.body.mid,
        )

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
    ) -> "CommentMessage":
        link = self._ignore_unsupported_parameters(
            link=link,
            notify=notify,
            keyboard=keyboard,
            media=media,
            attachments=attachments,
        )

        result = await self.bot.send_comment(
            message_id=self.unsafe_message.recipient.unsafe_post_id,
            text=text,
            link=link,
            format=format,
            disable_link_preview=disable_link_preview,
        )
        return result.message

    # Алиас сужает результат Message до CommentMessage
    answer = send_message  # type: ignore[mutable-override]

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
        comment = self.unsafe_message
        link = self._ignore_unsupported_parameters(
            link=link,
            notify=notify,
            keyboard=keyboard,
            media=media,
            attachments=attachments,
        )

        if text is None:
            text = comment.body.text

        return await self.bot.edit_comment(
            message_id=comment.recipient.unsafe_post_id,
            comment_id=comment.body.mid,
            text=text,
            link=link,
            format=format,
        )

    async def get_message_by_id(self, message_id: str) -> "CommentMessage":
        return await self.bot.get_comment_by_id(
            message_id=self.unsafe_message.recipient.unsafe_post_id,
            comment_id=message_id,
        )

    def _ignore_unsupported_parameters(
        self,
        link: NewMessageLink | None,
        notify: Omittable[bool],
        keyboard: Sequence[Sequence[InlineButtons]] | None,
        media: Sequence[MediaInput] | None,
        attachments: Sequence[AttachmentsRequests] | None,
    ) -> NewMessageLink | None:
        unsupported: list[str] = []
        if keyboard is not None:
            unsupported.append("keyboard")
        if media is not None:
            unsupported.append("media")
        if attachments is not None:
            unsupported.append("attachments")
        if is_defined(notify) and not notify:
            unsupported.append("notify=False")
        if link is not None and link.type is MessageLinkType.FORWARD:
            unsupported.append("link.type=forward")
            link = None

        if unsupported:
            loggers.methods.warning(
                "Параметры комментария не поддерживаются и будут проигнорированы: %s",
                ", ".join(unsupported),
            )
        return link

    delete_comment = delete_message
    send_comment = send_message
    edit_comment = edit_message
    get_comment_by_id = get_message_by_id
