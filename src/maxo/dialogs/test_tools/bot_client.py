import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

from maxo import Bot, Dispatcher
from maxo.bot.state import RunningBotState
from maxo.enums import ChatStatus, ChatType, MessageLinkType
from maxo.routing.signals import MaxoUpdate
from maxo.routing.updates import (
    BotAddedToChat,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
)
from maxo.types import (
    BotInfo,
    Callback,
    CallbackButton,
    Chat,
    LinkedMessage,
    Message,
    MessageBody,
    MessageStat,
    Recipient,
    User,
)

from .keyboard import InlineButtonLocator


class FakeBot(Bot):
    def __init__(self) -> None:
        super().__init__("", warming_up=False)
        info = BotInfo(
            user_id=1000,
            first_name="bot",
            username="bot",
            is_bot=True,
            last_activity_time=datetime.fromtimestamp(1234567890, tz=UTC),
        )
        self._state = RunningBotState(info=info, api_client=AsyncMock())

    async def answer_on_callback(self, *_: Any, **__: Any) -> None:
        pass

    def __hash__(self) -> int:
        return 1000

    def __eq__(self, other: object) -> bool:
        return self is other


class BotClient:
    def __init__(
        self,
        dp: Dispatcher,
        user_id: int = 1,
        chat_id: int = 1,
        chat_type: ChatType = ChatType.DIALOG,
        bot: Bot | None = None,
    ) -> None:
        self.chat = Chat(
            chat_id=chat_id,
            type=chat_type,
            status=ChatStatus.ACTIVE,
            last_event_time=datetime.now(UTC),
            is_public=False,
            participants_count=2,
        )
        self.user = User(
            user_id=user_id,
            is_bot=False,
            first_name=f"User_{user_id}",
            last_activity_time=datetime.now(UTC),
        )
        self.dp = dp
        self.last_update_id = 1
        self.last_message_id = 1
        self.bot = bot or FakeBot()

    def _new_update_id(self) -> int:
        self.last_update_id += 1
        return self.last_update_id

    def _new_message_id(self) -> int:
        self.last_message_id += 1
        return self.last_message_id

    def _new_message(
        self,
        text: str,
        reply_to: Message | None,
    ) -> Message:
        message_seq = self._new_message_id()
        return Message(
            sender=self.user,
            recipient=Recipient(
                chat_type=self.chat.type,
                user_id=self.bot.state.info.user_id,
                chat_id=self.chat.chat_id,
            ),
            timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
            link=(
                LinkedMessage(
                    type=MessageLinkType.REPLY,
                    sender=reply_to.sender,
                    chat_id=reply_to.recipient.chat_id,
                    message=reply_to.body,
                )
                if reply_to
                else None
            ),
            body=MessageBody(
                mid=str(message_seq),
                seq=message_seq,
                text=text,
            ),
            stat=MessageStat(
                views=1,
            ),
            url="https://max.ru/",
        )

    async def send(self, text: str, reply_to: Message | None = None) -> Any:
        return await self.dp.feed_update(
            MaxoUpdate(
                update=MessageCreated(
                    message=self._new_message(text, reply_to),
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                    user_locale="ru",
                ),
            ),
            self.bot,
        )

    async def send_channel_post(self, text: str) -> Any:
        """Эмулирует пост в канале: MessageCreated без sender (бот-админ)."""
        message_seq = self._new_message_id()
        msg = Message(
            recipient=Recipient(
                chat_type=ChatType.CHANNEL,
                user_id=self.bot.state.info.user_id,
                chat_id=self.chat.chat_id,
            ),
            timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
            body=MessageBody(
                mid=str(message_seq),
                seq=message_seq,
                text=text,
            ),
            stat=MessageStat(views=1),
            url="https://max.ru/",
        )
        return await self.dp.feed_update(
            MaxoUpdate(
                update=MessageCreated(
                    message=msg,
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                    user_locale="ru",
                ),
            ),
            self.bot,
        )

    async def send_channel_message_edited(self, text: str, mid: str) -> Any:
        """Эмулирует MessageEdited в канале без sender."""
        seq = int(mid) if mid.isdigit() else self._new_message_id()
        msg = Message(
            recipient=Recipient(
                chat_type=ChatType.CHANNEL,
                user_id=self.bot.state.info.user_id,
                chat_id=self.chat.chat_id,
            ),
            timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
            body=MessageBody(mid=mid, seq=seq, text=text),
            stat=MessageStat(views=1),
            url="https://max.ru/",
        )
        return await self.dp.feed_update(
            MaxoUpdate(
                update=MessageEdited(
                    message=msg,
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                ),
            ),
            self.bot,
        )

    async def send_channel_message_removed(self, mid: str) -> Any:
        """Эмулирует MessageRemoved в канале без sender."""
        return await self.dp.feed_update(
            MaxoUpdate(
                update=MessageRemoved(
                    message_id=mid,
                    chat_id=self.chat.chat_id,
                    user_id=self.bot.state.info.user_id,
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                ),
            ),
            self.bot,
        )

    def _new_callback(
        self,
        button: CallbackButton,
    ) -> Callback:
        if not button.payload:
            raise ValueError("Button has no callback data")
        return Callback(
            timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
            callback_id=str(uuid.uuid4()),
            payload=button.payload,
            user=self.user,
        )

    async def click(
        self,
        message: Message,
        locator: InlineButtonLocator,
    ) -> str:
        button = locator.find_button(message)
        if not button:
            raise ValueError(
                f"No button matching {locator} found",
            )

        callback = self._new_callback(button)
        await self.dp.feed_update(
            MaxoUpdate(
                update=MessageCallback(
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                    callback=callback,
                    message=message,
                    user_locale="ru",
                ),
            ),
            self.bot,
        )
        return callback.callback_id

    async def user_added_to_chat(self) -> Any:
        return await self.dp.feed_update(
            MaxoUpdate(
                update=UserAddedToChat(
                    chat_id=self.chat.chat_id,
                    is_channel=self.chat.type == ChatType.CHANNEL,
                    user=self.user,
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                ),
            ),
            self.bot,
        )

    async def bot_added_to_chat(self) -> Any:
        return await self.dp.feed_update(
            MaxoUpdate(
                update=BotAddedToChat(
                    chat_id=self.chat.chat_id,
                    is_channel=self.chat.type == ChatType.CHANNEL,
                    user=self.user,
                    timestamp=datetime.fromtimestamp(1234567890, tz=UTC),
                ),
            ),
            self.bot,
        )
