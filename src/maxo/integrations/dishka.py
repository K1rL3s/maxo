# ruff: noqa: SLF001

__all__ = ("CONTAINER_NAME", "MaxoProvider", "inject", "setup_dishka")

from collections.abc import Container, Generator
from functools import partial
from inspect import Parameter, signature
from typing import Any, ParamSpec, TypeVar, overload

from dishka import AsyncContainer

from maxo.routing.handlers.signal import SignalHandler, SignalHandlerFn
from maxo.routing.handlers.update import UpdateHandler, UpdateHandlerFn
from maxo.routing.interfaces import BaseRouter
from maxo.routing.interfaces.middleware import BaseMiddleware, NextMiddleware
from maxo.routing.observers import SignalObserver, UpdateObserver
from maxo.routing.signals.base import BaseSignal
from maxo.routing.signals.update import Update

try:
    from dishka import Provider, Scope, from_context
    from dishka.integrations.base import is_dishka_injected, wrap_injection
except ImportError as e:
    e.add_note(" * Please run `pip install maxo[dishka]`")
    raise

from maxo.bot.bot import Bot
from maxo.fsm.manager import FSMContext
from maxo.fsm.storages.base import BaseStorage, RawState
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.updates.base import BaseUpdate
from maxo.types.update_context import UpdateContext

CONTAINER_NAME = "dishka_container"

_ReturnT = TypeVar("_ReturnT")
_ParamsP = ParamSpec("_ParamsP")
_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)
_SignalT = TypeVar("_SignalT", bound=BaseSignal)
_Handler = TypeVar("_Handler", bound=UpdateHandler | SignalHandler)


# FIXME: Типы женерики функции сигналы хендлеры
# _SignalHandlerFn = Callable[_ParamsP, _ReturnT]
# _UpdateHandlerFn = Callable[[Concatenate[_UpdateT, _ParamsP]], _ReturnT]


# FIXME: Типы женерики функции сигналы хендлеры
@overload
def inject(
    func,  # _SignalHandlerFn[_SignalT, _ParamsP, _ReturnT],
) -> SignalHandlerFn[_SignalT, _ReturnT]: ...


# FIXME: Типы женерики функции сигналы хендлеры
@overload
def inject(
    func,  # : _UpdateHandlerFn[_UpdateT, _ParamsP, _ReturnT],
) -> UpdateHandlerFn[_UpdateT, _ReturnT]: ...


def inject(func):
    if CONTAINER_NAME in signature(func).parameters:
        additional_params = []
    else:
        additional_params = [
            Parameter(
                name=CONTAINER_NAME,
                annotation=Container,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ]

    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=lambda _, kwargs: kwargs[CONTAINER_NAME],
    )


def setup_dishka(
    container: AsyncContainer,
    dispatcher: Dispatcher,
    auto_inject: bool,
    extra_context: dict[Any, Any] | None = None,
) -> None:
    dispatcher.update.middleware.outer(
        DishkaMiddleware(container, extra_context),
    )

    if auto_inject:
        def _auto_inject(**_kwargs: Any) -> None:
            inject_router(dispatcher)

        dispatcher.before_startup.handler(_auto_inject)


def inject_router(router: BaseRouter) -> None:
    def chain_tail(router: BaseRouter) -> Generator[BaseRouter, None, None]:
        yield router
        for child_router in router.children_routers:
            yield from chain_tail(child_router)

    for sub_router in chain_tail(router):
        for observer in sub_router.observers.values():
            if not isinstance(observer, (UpdateObserver, SignalObserver)):
                continue

            for handler in observer.handlers:
                if not is_dishka_injected(handler._handler_fn):
                    inject_handler(handler)


def inject_handler(handler: _Handler) -> _Handler:
    temp_handler = type(handler)(
        handler_fn=inject(handler._handler_fn),
        filter=handler._filter,
    )

    handler._handler_fn = temp_handler._handler_fn
    handler._filter = temp_handler._filter
    handler._awaitable = temp_handler._awaitable
    handler._params = temp_handler._params
    handler._varkw = temp_handler._varkw

    return handler


class DishkaMiddleware(BaseMiddleware[Update[Any]]):
    __slots__ = ("_container", "_extra_context")

    def __init__(
        self,
        container: AsyncContainer,
        extra_context: dict[Any, Any] | None = None,
    ) -> None:
        self._container = container
        self._extra_context = extra_context or {}

    async def __call__(
        self,
        update: Update[Any],
        ctx: Ctx,
        next: NextMiddleware[Update[Any]],
    ) -> Any:
        async with self._container(
            {
                Update[Any]: update,
                Update[type(update.update)]: update,  # type: ignore[misc]
                Ctx: ctx,
            }
            | self._extra_context,
        ) as container:
            ctx[CONTAINER_NAME] = container
            return await next(ctx)


class MaxoProvider(Provider):
    scope = Scope.REQUEST

    context = (
        from_context(provides=Bot)
        + from_context(provides=Dispatcher)
        + from_context(provides=UpdateContext)
        + from_context(provides=BaseStorage)
        + from_context(provides=FSMContext)
        + from_context(provides=RawState)
        + from_context(provides=Update[Any])
        + from_context(provides=Update[_UpdateT])
        + from_context(provides=Ctx)
    )
