from typing import Any

from maxo import Ctx
from maxo.routing.events import MaxoUpdate
from maxo.routing.interfaces import BaseMiddleware, NextMiddleware
from maxo.routing.middlewares.update_context import UPDATE_CONTEXT_KEY, UpdateContext

from ..ids import MaxId
from ..user_repo import ExternalType, UserRepo


class CurrentUserMiddleware(BaseMiddleware[MaxoUpdate[Any]]):
    async def __call__(
        self,
        update: MaxoUpdate[Any],
        ctx: Ctx,
        next: NextMiddleware[MaxoUpdate[Any]],
    ) -> Any:
        user_repo: UserRepo = ctx["user_repo"]
        update_context: UpdateContext = ctx[UPDATE_CONTEXT_KEY]

        if update_context.user_id:
            user = await user_repo.get_or_create_user(
                external_id=MaxId(update_context.user_id),
                external_type=ExternalType.MAX,
            )
            ctx["current_user"] = user

        return await next(ctx)
