import functools
from typing import Any

import pytest

from maxo.enums import ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import BaseFilter, Command
from maxo.routing.flags import HANDLER_KEY, extract_flags, flags, get_flag
from maxo.routing.interfaces.middleware import NextMiddleware
from maxo.routing.observers.base import bind_handler
from maxo.routing.routers.simple import Router
from maxo.routing.signals import BeforeStartup, MaxoUpdate
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW
from tests.factories import make_bot, make_flagged_handler


@pytest.fixture
def update() -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text="/start"),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
    )


async def handler(update: MessageCreated) -> str:
    return "OK"


class TestRegistration:
    def test_flags_via_decorator_kwarg(self) -> None:
        router = Router()

        router.message_created(flags={"rate_limit": 5})(handler)

        assert router.message_created.handlers[0].flags == {"rate_limit": 5}

    def test_flags_via_register(self) -> None:
        router = Router()

        router.message_created.register(handler, flags={"rate_limit": 5})

        assert router.message_created.handlers[0].flags == {"rate_limit": 5}

    def test_flags_via_handler_method(self) -> None:
        router = Router()

        router.message_created.handler(handler, flags={"rate_limit": 5})

        assert router.message_created.handlers[0].flags == {"rate_limit": 5}

    def test_flags_via_function_decorator(self) -> None:
        router = Router()

        @router.message_created()
        @flags.chat_action
        async def marked(update: MessageCreated) -> None:
            pass

        assert router.message_created.handlers[0].flags == {"chat_action": True}

    def test_no_flags_by_default(self) -> None:
        router = Router()

        router.message_created.handler(handler)

        assert router.message_created.handlers[0].flags == {}

    def test_function_decorator_wins_over_kwarg(self) -> None:
        router = Router()

        @router.message_created(flags={"chat_action": "typing_on", "spam": "eggs"})
        @flags.chat_action("sending_photo")
        async def marked(update: MessageCreated) -> None:
            pass

        assert router.message_created.handlers[0].flags == {
            "chat_action": "sending_photo",
            "spam": "eggs",
        }

    def test_passed_flags_are_copied(self) -> None:
        router = Router()
        source: dict[str, Any] = {"rate_limit": 5}

        router.message_created.handler(handler, flags=source)
        source["rate_limit"] = 100

        assert router.message_created.handlers[0].flags == {"rate_limit": 5}

    def test_flags_above_wrapping_decorator(self) -> None:
        router = Router()

        def wrap(fn: Any) -> Any:
            @functools.wraps(fn)
            async def wrapper(update: MessageCreated) -> Any:
                return await fn(update)

            return wrapper

        @router.message_created()
        @flags.chat_action("sending_photo")
        @wrap
        async def marked(update: MessageCreated) -> None:
            pass

        assert router.message_created.handlers[0].flags == {
            "chat_action": "sending_photo",
        }

    def test_signal_observer_supports_flags(self) -> None:
        router = Router()

        async def on_startup() -> None:
            pass

        router.after_startup.handler(on_startup, flags={"spam": "eggs"})

        assert router.after_startup.handlers[-1].flags == {"spam": "eggs"}


class TestFiltersUpdateFlags:
    def test_filter_can_extend_flags(self) -> None:
        class MarkingFilter(BaseFilter[MessageCreated]):
            async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
                return True

            def update_handler_flags(self, flags: dict[str, Any]) -> None:
                flags["marked"] = True

        router = Router()
        router.message_created.handler(handler, MarkingFilter())

        assert router.message_created.handlers[0].flags == {"marked": True}

    def test_base_filter_does_nothing_by_default(self) -> None:
        class PlainFilter(BaseFilter[MessageCreated]):
            async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
                return True

        router = Router()
        router.message_created.handler(handler, PlainFilter())

        assert router.message_created.handlers[0].flags == {}

    def test_command_filter_registers_commands_flag(self) -> None:
        router = Router()
        command = Command("start")

        router.message_created.handler(handler, command)

        assert router.message_created.handlers[0].flags == {"commands": [command]}

    def test_filters_do_not_mutate_shared_flags(self) -> None:
        router = Router()
        shared: dict[str, Any] = {"commands": []}
        start = Command("start")
        help_ = Command("help")

        router.message_created.handler(handler, start, flags=shared)
        router.message_created.handler(handler, help_, flags=shared)

        assert shared == {"commands": []}
        assert router.message_created.handlers[0].flags == {"commands": [start]}
        assert router.message_created.handlers[1].flags == {"commands": [help_]}

    def test_several_command_filters_accumulate(self) -> None:
        router = Router()
        start = Command("start")
        help_ = Command("help")

        router.message_created.handler(handler, start, help_)

        assert router.message_created.handlers[0].flags == {
            "commands": [start, help_],
        }

    def test_logic_filters_register_nested_commands_flag(self) -> None:
        start = Command("start")
        help_ = Command("help")

        for logic_filter in (start | help_, start & help_):
            router = Router()
            router.message_created.handler(handler, logic_filter)

            assert router.message_created.handlers[0].flags == {
                "commands": [start, help_],
            }

    def test_inverted_filter_does_not_register_nested_flags(self) -> None:
        router = Router()

        router.message_created.handler(handler, ~Command("start"))

        assert router.message_created.handlers[0].flags == {}

    def test_inversion_inside_logic_filter_does_not_register_nested_flags(
        self,
    ) -> None:
        router = Router()
        help_ = Command("help")

        router.message_created.handler(handler, help_ & ~Command("start"))

        assert router.message_created.handlers[0].flags == {"commands": [help_]}


class TestFlagsInRuntime:
    async def test_flag_above_registration_is_visible_in_middleware(
        self,
        ctx: Ctx,
    ) -> None:
        dp = Dispatcher()
        seen: list[Any] = []

        @flags.chat_action
        @dp.message_created()
        async def marked(update: MessageCreated) -> str:
            return "OK"

        async def middleware(
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            seen.append(get_flag(ctx, "chat_action"))
            return await next(ctx)

        dp.message_created.middleware(middleware)

        await dp.feed_signal(BeforeStartup())
        assert await dp.trigger(ctx) == "OK"
        assert seen == [True]

    def test_nested_bind_restores_previous_handler(self) -> None:
        previous = make_flagged_handler(previous=True)
        outer = make_flagged_handler(outer=True)
        inner = make_flagged_handler(inner=True)
        ctx = Ctx({HANDLER_KEY: previous})

        with bind_handler(ctx, outer):
            with bind_handler(ctx, inner):
                assert ctx[HANDLER_KEY] is inner

            assert ctx[HANDLER_KEY] is outer

        assert ctx[HANDLER_KEY] is previous

    async def test_handler_is_available_in_ctx(self, ctx: Ctx) -> None:
        dp = Dispatcher()
        seen: list[Any] = []

        @dp.message_created(flags={"rate_limit": 5})
        async def marked(update: MessageCreated) -> str:
            return "OK"

        async def middleware(
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            seen.append(get_flag(ctx, "rate_limit"))
            return await next(ctx)

        dp.message_created.middleware(middleware)

        await dp.feed_signal(BeforeStartup())
        assert await dp.trigger(ctx) == "OK"
        assert seen == [5]

    async def test_flags_are_visible_in_filters(self, ctx: Ctx) -> None:
        dp = Dispatcher()
        seen: list[dict[str, Any]] = []

        class SpyFilter(BaseFilter[MessageCreated]):
            async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
                seen.append(extract_flags(ctx))
                return True

        dp.message_created.handler(handler, SpyFilter(), flags={"spam": "eggs"})

        await dp.feed_signal(BeforeStartup())
        await dp.trigger(ctx)

        assert seen == [{"spam": "eggs"}]

    async def test_flags_do_not_leak_to_child_router(self, ctx: Ctx) -> None:
        dp = Dispatcher()
        child = Router("child")
        dp.include(child)
        seen: list[dict[str, Any]] = []

        class RejectingFilter(BaseFilter[MessageCreated]):
            async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
                return False

        dp.message_created.handler(handler, RejectingFilter(), flags={"spam": "eggs"})

        async def middleware(
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            seen.append(extract_flags(ctx))
            return await next(ctx)

        child.message_created.middleware.outer(middleware)
        child.message_created.handler(handler)

        await dp.feed_signal(BeforeStartup())
        assert await dp.trigger(ctx) == "OK"
        assert seen == [{}]

    async def test_internal_handler_does_not_leak_to_outer_middleware(
        self,
        update: MessageCreated,
    ) -> None:
        dp = Dispatcher(disable_fsm=True)
        seen: list[bool] = []

        async def middleware(
            update: MessageCreated,
            ctx: Ctx,
            next: NextMiddleware[MessageCreated],
        ) -> Any:
            seen.append(HANDLER_KEY in ctx)
            return await next(ctx)

        dp.message_created.middleware.outer(middleware)
        dp.message_created.handler(handler)

        await dp.feed_signal(BeforeStartup())
        assert await dp.feed_max_update(MaxoUpdate(update=update), make_bot()) == "OK"
        assert seen == [False]

    async def test_handler_key_is_cleaned_when_unhandled(self, ctx: Ctx) -> None:
        dp = Dispatcher()

        class RejectingFilter(BaseFilter[MessageCreated]):
            async def __call__(self, update: MessageCreated, ctx: Ctx) -> bool:
                return False

        dp.message_created.handler(handler, RejectingFilter())

        await dp.feed_signal(BeforeStartup())
        await dp.trigger(ctx)

        assert HANDLER_KEY not in ctx
