import random
from datetime import UTC, datetime
from uuid import uuid4

from maxo import Bot
from maxo.dialogs import ShowMode
from maxo.dialogs.api.entities import NewMessage, OldMessage
from maxo.dialogs.api.protocols import (
    MessageManagerProtocol,
    MessageNotModified,
)
from maxo.enums import AttachmentType
from maxo.types import (
    Attachments,
    Callback,
    InlineKeyboardAttachment,
    Keyboard,
    Message,
    MessageBody,
    PhotoAttachment,
    PhotoAttachmentPayload,
    Recipient,
)


class MockMessageManager(MessageManagerProtocol):
    def __init__(self) -> None:
        self.answered_callbacks: set[str] = set()
        self.sent_messages: list[Message] = []
        self.last_message_id = 0

    def reset_history(self) -> None:
        self.sent_messages.clear()
        self.answered_callbacks.clear()

    def assert_one_message(self) -> None:
        assert len(self.sent_messages) == 1

    def last_message(self) -> Message:
        return self.sent_messages[-1]

    def first_message(self) -> Message:
        return self.sent_messages[0]

    def one_message(self) -> Message:
        self.assert_one_message()
        return self.first_message()

    async def remove_kbd(
        self,
        bot: Bot,
        show_mode: ShowMode,
        old_message: OldMessage | None,
    ) -> None:
        if not old_message:
            return
        if show_mode in (ShowMode.DELETE_AND_SEND, ShowMode.NO_UPDATE):
            return
        assert isinstance(old_message, OldMessage)

        new_attachments = [
            attach
            for attach in old_message.attachments
            if attach.type != AttachmentType.INLINE_KEYBOARD
        ]

        # `OldMessage.text` может быть `UnknownText.UNKNOWN`, если сообщение
        # восстановлено из стека, а не пришло в апдейте.
        old_text = old_message.text
        text = old_text if isinstance(old_text, str) else None

        message = Message(
            timestamp=datetime.now(UTC),
            recipient=Recipient(
                chat_type=old_message.recipient.chat_type,
                chat_id=old_message.recipient.chat_id,
                user_id=old_message.recipient.user_id,
            ),
            body=MessageBody(
                mid=old_message.message_id,
                seq=old_message.sequence_id,
                text=text,
                attachments=new_attachments,
            ),
        )
        self.sent_messages.append(message)

    async def answer_callback(
        self,
        bot: Bot,
        callback: Callback,
    ) -> None:
        self.answered_callbacks.add(callback.callback_id)

    def assert_answered(self, callback_id: str) -> None:
        assert callback_id in self.answered_callbacks

    async def show_message(
        self,
        bot: Bot,
        new_message: NewMessage,
        old_message: OldMessage | None,
    ) -> OldMessage:
        assert isinstance(new_message, NewMessage)
        assert isinstance(old_message, (OldMessage, type(None)))
        if new_message.show_mode is ShowMode.NO_UPDATE:
            raise MessageNotModified

        message_id = self.last_message_id + 1
        self.last_message_id = message_id

        converted_attachments: list[Attachments] = []
        for media in new_message.media:
            if media.type == AttachmentType.IMAGE:
                converted_attachments.append(
                    PhotoAttachment(
                        payload=PhotoAttachmentPayload(
                            photo_id=random.randint(1, 1_000_000),
                            token=(
                                media.media_id.token if media.media_id else str(uuid4())
                            ),
                            url=media.url or "",
                        ),
                    ),
                )
            else:
                raise NotImplementedError(
                    f"Unsupported media type in mock: {media.type}",
                )

        keyboard = new_message.keyboard
        if keyboard:
            converted_attachments.append(
                InlineKeyboardAttachment(payload=Keyboard(buttons=keyboard)),
            )

        self.sent_messages.append(
            Message(
                sender=bot.info,
                recipient=new_message.recipient,
                timestamp=datetime.now(UTC),
                body=MessageBody(
                    mid=str(message_id),
                    seq=message_id,
                    text=new_message.text,
                    attachments=converted_attachments,
                ),
            ),
        )

        return OldMessage(
            message_id=str(message_id),
            sequence_id=message_id,
            recipient=new_message.recipient,
            text=new_message.text,
            attachments=converted_attachments,
        )
