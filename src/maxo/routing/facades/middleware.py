from collections.abc import Mapping
from typing import Any

from maxo.routing.ctx import Ctx
from maxo.routing.facades import (
    BaseUpdateFacade,
    BotAddedToChatFacade,
    BotRemovedFromChatFacade,
    BotStartedFacade,
    BotStoppedFacade,
    ChatTitleChangedFacade,
    DialogClearedFacade,
    DialogMutedFacade,
    DialogRemovedFacade,
    DialogUnmutedFacade,
    ErrorEventFacade,
    MessageCallbackFacade,
    MessageCreatedFacade,
    MessageEditedFacade,
    MessageRemovedFacade,
    UserAddedToChatFacade,
    UserRemovedFromChatFacade,
)
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.signals.update import MaxoUpdate
from maxo.routing.updates import (
    BaseUpdate,
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    ChatTitleChanged,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    ErrorEvent,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
    UserRemovedFromChat,
)

FACADE_KEY = "facade"

_FACADES_MAP: Mapping[type[Any], type[BaseUpdateFacade[Any]]] = {
    MessageCreated: MessageCreatedFacade,
    MessageCallback: MessageCallbackFacade,
    BotAddedToChat: BotAddedToChatFacade,
    BotRemovedFromChat: BotRemovedFromChatFacade,
    BotStarted: BotStartedFacade,
    BotStopped: BotStoppedFacade,
    ChatTitleChanged: ChatTitleChangedFacade,
    DialogCleared: DialogClearedFacade,
    DialogMuted: DialogMutedFacade,
    DialogRemoved: DialogRemovedFacade,
    DialogUnmuted: DialogUnmutedFacade,
    ErrorEvent: ErrorEventFacade,
    MessageEdited: MessageEditedFacade,
    MessageRemoved: MessageRemovedFacade,
    UserAddedToChat: UserAddedToChatFacade,
    UserRemovedFromChat: UserRemovedFromChatFacade,
}


class FacadeMiddleware(BaseMiddleware[MaxoUpdate[Any]]):
    async def __call__(
        self,
        update: MaxoUpdate[Any],
        ctx: Ctx,
        next: NextMiddleware[MaxoUpdate[Any]],
    ) -> Any:
        facade = self._facade_cls_factory(type(update.update))
        if facade:
            ctx[FACADE_KEY] = facade(ctx["bot"], update.update)

        return await next(ctx)

    def _facade_cls_factory(
        self,
        update_tp: type[BaseUpdate],
    ) -> type[BaseUpdateFacade[Any]] | None:
        return _FACADES_MAP.get(update_tp)
