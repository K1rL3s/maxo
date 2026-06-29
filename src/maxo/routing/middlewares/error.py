from typing import Any

from maxo import Bot
from maxo.routing.ctx import Ctx
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.interfaces.router import BaseRouter
from maxo.routing.sentinels import UNHANDLED, CancelHandler, SkipHandler
from maxo.routing.updates.error import ErrorEvent


class ErrorMiddleware(BaseMiddleware[Any]):
    __slots__ = ("_router",)

    def __init__(self, router: BaseRouter) -> None:
        self._router = router

    async def __call__(self, update: Any, ctx: Ctx, next: NextMiddleware[Any]) -> Any:
        try:
            return await next(ctx)
        except (SkipHandler, CancelHandler):  # pragma: no cover
            raise
        except Exception as exception:
            bot: Bot = ctx["bot"]
            exception_event = ErrorEvent(
                exception=exception,
                update=update,
            ).as_(bot)
            new_ctx = Ctx(dict(ctx))
            new_ctx["update"] = exception_event
            result = await self._router.trigger(new_ctx)
            if result is UNHANDLED:
                raise
            return result
