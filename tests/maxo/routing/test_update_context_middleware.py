from datetime import UTC, datetime
from typing import Any

import pytest

from maxo.enums import ChatStatus, ChatType
from maxo.routing.ctx import Ctx
from maxo.routing.middlewares.update_context import (
    EVENT_CHAT_KEY,
    EVENT_FROM_USER_KEY,
    UPDATE_CONTEXT_KEY,
    UpdateContextMiddleware,
)
from maxo.routing.signals import MaxoUpdate
from maxo.routing.updates import (
    BotAddedToChat,
    BotRemovedFromChat,
    BotStarted,
    BotStopped,
    ChatTitleChanged,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    MessageCallback,
    MessageCreated,
    MessageEdited,
    MessageRemoved,
    UserAddedToChat,
    UserRemovedFromChat,
)
from maxo.types import (
    Callback,
    Chat,
    ChatMember,
    ChatMembersList,
    Message,
    MessageBody,
    Recipient,
    User,
    UserWithPhoto,
)


class MockBot:
    def __init__(self, *, get_chat: Any, get_members: Any) -> None:
        self._get_chat = get_chat
        self._get_members = get_members

    async def get_chat(self, **kwargs: Any) -> Any:
        return await self._get_chat(self, **kwargs)

    async def get_members(self, **kwargs: Any) -> Any:
        return await self._get_members(self, **kwargs)


def make_user(user_id: int = 1, first_name: str = "Test") -> User:
    return User(
        user_id=user_id,
        first_name=first_name,
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )


def make_message_created(chat_id: int = 1, user_id: int = 1) -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="m1", seq=1),
            recipient=Recipient(chat_type=ChatType.CHAT, chat_id=chat_id),
            timestamp=datetime.now(UTC),
            sender=make_user(user_id=user_id),
        ),
        timestamp=datetime.now(UTC),
    )


def make_message_removed(chat_id: int = 1, user_id: int = 2) -> MessageRemoved:
    return MessageRemoved(
        chat_id=chat_id,
        message_id="m1",
        user_id=user_id,
        timestamp=datetime.now(UTC),
    )


async def run_middleware(
    middleware: UpdateContextMiddleware,
    inner_update: Any,
    ctx: Ctx,
) -> None:
    update = MaxoUpdate(update=inner_update)
    next_called = False

    async def next_handler(ctx: Ctx) -> Any:
        nonlocal next_called
        next_called = True
        return None

    await middleware(update=update, ctx=ctx, next=next_handler)
    assert next_called


@pytest.mark.parametrize(
    (
        "update",
        "expected_chat_id",
        "expected_user_id",
        "expected_type",
        "expect_event_user",
    ),
    [
        (
            BotAddedToChat(
                chat_id=10,
                is_channel=False,
                user=make_user(1),
                timestamp=datetime.now(UTC),
            ),
            10,
            1,
            ChatType.CHAT,
            True,
        ),
        (
            BotRemovedFromChat(
                chat_id=11,
                is_channel=True,
                user=make_user(2),
                timestamp=datetime.now(UTC),
            ),
            11,
            2,
            ChatType.CHANNEL,
            True,
        ),
        (
            BotStarted(chat_id=12, user=make_user(3), timestamp=datetime.now(UTC)),
            12,
            3,
            ChatType.DIALOG,
            True,
        ),
        (
            BotStopped(chat_id=13, user=make_user(4), timestamp=datetime.now(UTC)),
            13,
            4,
            ChatType.DIALOG,
            True,
        ),
        (
            ChatTitleChanged(
                chat_id=14,
                title="New title",
                user=make_user(5),
                timestamp=datetime.now(UTC),
            ),
            14,
            5,
            None,
            True,
        ),
        (
            DialogCleared(
                chat_id=15,
                user=make_user(6),
                user_locale="ru",
                timestamp=datetime.now(UTC),
            ),
            15,
            6,
            ChatType.DIALOG,
            True,
        ),
        (
            DialogMuted(
                chat_id=16,
                muted_until=datetime.now(UTC),
                user=make_user(7),
                user_locale="ru",
                timestamp=datetime.now(UTC),
            ),
            16,
            7,
            ChatType.DIALOG,
            True,
        ),
        (
            DialogRemoved(
                chat_id=17,
                user=make_user(8),
                user_locale="ru",
                timestamp=datetime.now(UTC),
            ),
            17,
            8,
            ChatType.DIALOG,
            True,
        ),
        (
            DialogUnmuted(
                chat_id=18,
                user=make_user(9),
                user_locale="ru",
                timestamp=datetime.now(UTC),
            ),
            18,
            9,
            ChatType.DIALOG,
            True,
        ),
        (
            UserAddedToChat(
                chat_id=19,
                is_channel=False,
                user=make_user(10),
                timestamp=datetime.now(UTC),
            ),
            19,
            10,
            ChatType.CHAT,
            True,
        ),
        (
            UserRemovedFromChat(
                chat_id=20,
                is_channel=True,
                user=make_user(11),
                timestamp=datetime.now(UTC),
            ),
            20,
            11,
            ChatType.CHANNEL,
            True,
        ),
        (
            MessageCallback(
                callback=Callback(
                    callback_id="cb-1",
                    timestamp=datetime.now(UTC),
                    user=make_user(12),
                ),
                message=make_message_created(chat_id=21, user_id=100).message,
                timestamp=datetime.now(UTC),
            ),
            21,
            12,
            ChatType.CHAT,
            True,
        ),
        (
            MessageEdited(
                message=make_message_created(chat_id=22, user_id=13).message,
                timestamp=datetime.now(UTC),
            ),
            22,
            13,
            ChatType.CHAT,
            True,
        ),
        (make_message_created(chat_id=23, user_id=14), 23, 14, ChatType.CHAT, True),
        (make_message_removed(chat_id=24, user_id=15), 24, 15, None, False),
    ],
)
async def test_resolve_update_context_for_all_update_types(
    update: Any,
    expected_chat_id: int,
    expected_user_id: int,
    expected_type: ChatType | None,
    expect_event_user: bool,
) -> None:
    middleware = UpdateContextMiddleware()
    ctx = Ctx({"update": update})

    await run_middleware(middleware, update, ctx)

    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat_id == expected_chat_id
    assert update_context.user_id == expected_user_id
    assert update_context.type == expected_type
    assert update_context.chat is None

    if expect_event_user:
        assert update_context.user is not None
        assert ctx[EVENT_FROM_USER_KEY] is update_context.user
    else:
        assert update_context.user is None
        assert EVENT_FROM_USER_KEY not in ctx


async def test_resolve_message_created_without_enrich() -> None:
    middleware = UpdateContextMiddleware()
    msg = make_message_created(chat_id=10, user_id=5)
    ctx = Ctx({"update": msg})

    await run_middleware(middleware, msg, ctx)

    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat_id == 10
    assert update_context.user_id == 5
    assert update_context.chat is None
    assert update_context.user is msg.message.sender
    assert update_context.type == ChatType.CHAT
    assert ctx[EVENT_FROM_USER_KEY] is msg.message.sender


async def test_resolve_message_removed_without_enrich() -> None:
    middleware = UpdateContextMiddleware()
    removed = make_message_removed(chat_id=20, user_id=7)
    ctx = Ctx({"update": removed})

    await run_middleware(middleware, removed, ctx)

    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat_id == 20
    assert update_context.user_id == 7
    assert update_context.chat is None
    assert update_context.user is None
    assert update_context.type is None
    assert EVENT_FROM_USER_KEY not in ctx


async def test_enrich_disabled_does_not_call_bot() -> None:
    async def get_chat(_: Any, /, **__: Any) -> None:
        raise AssertionError("get_chat must not be called")

    async def get_members(_: Any, /, **__: Any) -> None:
        raise AssertionError("get_members must not be called")

    bot = MockBot(get_chat=get_chat, get_members=get_members)
    middleware = UpdateContextMiddleware(enrich=False)
    msg = make_message_created()
    ctx = Ctx({"update": msg, "bot": bot})

    await run_middleware(middleware, msg, ctx)

    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat is None


async def test_enrich_enabled_fills_chat_and_user_from_payload() -> None:
    chat_result = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=2,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
    )

    get_chat_called: list[int] = []

    async def get_chat(_: Any, /, chat_id: int, **__: Any) -> Chat:
        get_chat_called.append(chat_id)
        return chat_result

    async def get_members_noop(_: Any, /, **__: Any) -> ChatMembersList:
        return ChatMembersList(members=[])

    bot = MockBot(get_chat=get_chat, get_members=get_members_noop)
    middleware = UpdateContextMiddleware(enrich=True)
    msg = make_message_created(chat_id=1, user_id=5)
    ctx = Ctx({"update": msg, "bot": bot})

    await run_middleware(middleware, msg, ctx)

    assert get_chat_called == [1]
    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat is chat_result
    assert update_context.type == ChatType.CHAT
    assert update_context.user is msg.message.sender
    assert ctx[EVENT_FROM_USER_KEY] is msg.message.sender


async def test_enrich_message_removed_fills_user() -> None:
    chat_result = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=2,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
    )
    member = ChatMember(
        user_id=2,
        first_name="Member",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
        alias="",
        is_admin=False,
        is_owner=False,
        join_time=datetime.now(UTC),
        last_access_time=datetime.now(UTC),
    )
    members_list = ChatMembersList(members=[member])

    get_chat_calls: list[int] = []
    get_members_calls: list[tuple[int, list[int]]] = []

    async def get_chat(_: Any, /, chat_id: int, **__: Any) -> Chat:
        get_chat_calls.append(chat_id)
        return chat_result

    async def get_members(
        _: Any,
        /,
        chat_id: int,
        user_ids: list[int],
        **__: Any,
    ) -> ChatMembersList:
        get_members_calls.append((chat_id, user_ids))
        return members_list

    bot = MockBot(get_chat=get_chat, get_members=get_members)
    middleware = UpdateContextMiddleware(enrich=True)
    removed = make_message_removed(chat_id=1, user_id=2)
    ctx = Ctx({"update": removed, "bot": bot})

    await run_middleware(middleware, removed, ctx)

    assert get_chat_calls == [1]
    assert get_members_calls == [(1, [2])]
    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat is chat_result
    assert update_context.user is member
    assert ctx[EVENT_FROM_USER_KEY] is member


async def test_enrich_message_removed_dialog_fills_user() -> None:
    dialog_user = UserWithPhoto(
        user_id=3,
        first_name="DialogUser",
        is_bot=False,
        last_activity_time=datetime.now(UTC),
    )
    chat_result = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=2,
        status=ChatStatus.ACTIVE,
        type=ChatType.DIALOG,
        dialog_with_user=dialog_user,
    )

    get_chat_calls: list[int] = []

    async def get_chat(_: Any, /, chat_id: int, **__: Any) -> Chat:
        get_chat_calls.append(chat_id)
        return chat_result

    async def get_members_must_not_be_called(_: Any, **__: Any) -> None:
        raise AssertionError("get_members must not be called for DIALOG")

    bot = MockBot(
        get_chat=get_chat,
        get_members=get_members_must_not_be_called,
    )
    middleware = UpdateContextMiddleware(enrich=True)
    removed = make_message_removed(chat_id=1, user_id=3)
    ctx = Ctx({"update": removed, "bot": bot})

    await run_middleware(middleware, removed, ctx)

    assert get_chat_calls == [1]
    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat is chat_result
    assert update_context.user is dialog_user
    assert ctx[EVENT_FROM_USER_KEY] is dialog_user


async def test_enrich_enabled_fills_chat_and_event_chat_key() -> None:
    chat_result = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=datetime.now(UTC),
        participants_count=2,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
    )

    get_chat_called: list[int] = []

    async def get_chat(_: Any, /, chat_id: int, **__: Any) -> Chat:
        get_chat_called.append(chat_id)
        return chat_result

    async def get_members_noop(_: Any, /, **__: Any) -> ChatMembersList:
        return ChatMembersList(members=[])

    bot = MockBot(get_chat=get_chat, get_members=get_members_noop)
    middleware = UpdateContextMiddleware(enrich=True)
    msg = make_message_created(chat_id=1, user_id=5)
    ctx = Ctx({"update": msg, "bot": bot})

    await run_middleware(middleware, msg, ctx)

    assert get_chat_called == [1]
    update_context = ctx[UPDATE_CONTEXT_KEY]
    assert update_context.chat is chat_result
    assert ctx[EVENT_CHAT_KEY] is chat_result
