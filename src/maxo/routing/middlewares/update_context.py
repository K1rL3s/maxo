from typing import Any, Final

from maxo import loggers
from maxo.enums import ChatType
from maxo.omit import is_defined
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.updates.bot_added_to_chat import BotAddedToChat
from maxo.routing.updates.bot_removed_from_chat import BotRemovedFromChat
from maxo.routing.updates.bot_started import BotStarted
from maxo.routing.updates.bot_stopped import BotStopped
from maxo.routing.updates.chat_title_changed import ChatTitleChanged
from maxo.routing.updates.dialog_cleared import DialogCleared
from maxo.routing.updates.dialog_muted import DialogMuted
from maxo.routing.updates.dialog_removed import DialogRemoved
from maxo.routing.updates.dialog_unmuted import DialogUnmuted
from maxo.routing.updates.message_callback import MessageCallback
from maxo.routing.updates.message_created import MessageCreated
from maxo.routing.updates.message_edited import MessageEdited
from maxo.routing.updates.message_removed import MessageRemoved
from maxo.routing.updates.user_added_to_chat import UserAddedToChat
from maxo.routing.updates.user_removed_from_chat import UserRemovedFromChat
from maxo.types import User
from maxo.types.update_context import UpdateContext

UPDATE_CONTEXT_KEY: Final = "update_context"
EVENT_FROM_USER_KEY: Final = "event_from_user"
EVENT_CHAT_KEY: Final = "event_chat"

# Подражание aiogram
EVENT_CONTEXT_KEY: Final = "event_context"  # same as UPDATE_CONTEXT_KEY


class UpdateContextMiddleware(BaseMiddleware[MaxoUpdate[Any]]):
    """
    Мидлварь, заполняющий контекст апдейта (chat_id, user_id.

    При обогащении - chat, user.

    Args:
        enrich: при True запрашивать чат и при необходимости пользователя через Bot API.
        Можно также передать enrich_update_context=True в workflow_data
        (например при LongPolling.run).

    """

    def __init__(self, enrich: bool = False) -> None:
        self._enrich = enrich

    async def __call__(
        self,
        update: MaxoUpdate[Any],
        ctx: Ctx,
        next: NextMiddleware[MaxoUpdate[Any]],
    ) -> Any:
        do_enrich = self._enrich or ctx.get("enrich_update_context", False)
        update_context = await self._resolve_update_context(
            update.update,
            ctx,
            do_enrich,
        )

        ctx[UPDATE_CONTEXT_KEY] = update_context
        ctx[EVENT_CONTEXT_KEY] = update_context
        if update_context.user is not None:
            ctx[EVENT_FROM_USER_KEY] = update_context.user
        if update_context.chat is not None:
            ctx[EVENT_CHAT_KEY] = update_context.chat

        return await next(ctx)

    async def _enrich_context(self, ctx: Ctx, update_context: UpdateContext) -> None:
        """Дополняет контекст данными чата и пользователя через Bot API."""
        bot = ctx["bot"]

        if update_context.chat_id is not None and update_context.chat is None:
            try:
                loggers.update_context.debug(
                    "Обогащение контекста чатом: chat_id=%s",
                    update_context.chat_id,
                )
                chat = await bot.get_chat(chat_id=update_context.chat_id)
                update_context.chat = chat
                update_context.type = chat.type
            except Exception:  # noqa: BLE001
                loggers.update_context.warning(
                    "Не удалось обогатить контекст чатом",
                    exc_info=True,
                )

        if update_context.chat is not None and is_defined(
            update_context.chat.dialog_with_user,
        ):
            update_context.user = update_context.chat.unsafe_dialog_with_user
        elif (
            update_context.user_id is not None
            and update_context.chat_id is not None
            and update_context.user is None
        ):
            chat_id = update_context.chat_id
            user_id = update_context.user_id
            try:
                members = await bot.get_members(chat_id=chat_id, user_ids=[user_id])
                if members.members:
                    update_context.user = members.members[0]
                else:
                    raise ValueError(  # noqa: TRY301
                        f"Юзер user_id={user_id} не найден в чате chat_id={chat_id}",
                    )
            except Exception:  # noqa: BLE001
                loggers.update_context.warning(
                    "Не удалось загрузить участника чата",
                    exc_info=True,
                )

    async def _resolve_update_context(
        self,
        update: Any,
        ctx: Ctx,
        do_enrich: bool,
    ) -> UpdateContext:
        # Deferred import to avoid circular dependency:
        # update_context -> dialogs -> fsm -> update_context
        from maxo.dialogs.api.entities import DialogUpdateEvent  # noqa: PLC0415

        chat_id = None
        user_id = None
        chat_type: ChatType | None = None
        user: User | None = None

        if isinstance(
            update,
            (
                BotStarted,
                BotStopped,
                DialogCleared,
                DialogMuted,
                DialogRemoved,
                DialogUnmuted,
            ),
        ):
            user = update.user
            user_id = user.id
            chat_id = update.chat_id
            chat_type = ChatType.DIALOG
        elif isinstance(
            update,
            (
                BotAddedToChat,
                BotRemovedFromChat,
                UserAddedToChat,
                UserRemovedFromChat,
                ChatTitleChanged,
            ),
        ):
            user = update.user
            user_id = user.id
            chat_id = update.chat_id
            if hasattr(update, "is_channel"):
                chat_type = ChatType.CHANNEL if update.is_channel else ChatType.CHAT
        elif isinstance(update, MessageCallback):
            user = update.user
            user_id = user.id
            if (_message := update.message) is not None:
                chat_id = _message.recipient.chat_id
                chat_type = _message.recipient.chat_type
        elif isinstance(update, (MessageEdited, MessageCreated)):
            user = update.message.sender if is_defined(update.message.sender) else None
            user_id = user.id if user is not None else None
            _recipient = update.message.recipient
            chat_id = _recipient.chat_id
            chat_type = _recipient.chat_type
        elif isinstance(update, MessageRemoved):
            chat_id = update.chat_id
            user_id = update.user_id
        elif isinstance(update, DialogUpdateEvent):
            user = update.user
            user_id = user.id
            chat_id = update.recipient.chat_id
            chat_type = update.recipient.chat_type

        update_context = UpdateContext(
            chat_id=chat_id,
            user_id=user_id,
            type=chat_type,
            user=user,
        )
        if do_enrich and "bot" in ctx:
            await self._enrich_context(ctx, update_context)

        return update_context
