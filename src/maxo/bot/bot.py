import json
import pathlib
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any, BinaryIO, Self, TypeVar

from adaptix import Retort
from aiohttp import ClientTimeout
from unihttp.bind_method import bind_method
from unihttp.clients.base import BaseAsyncClient
from unihttp.method import BaseMethod, ResponseType
from unihttp.middlewares import AsyncMiddleware

from maxo import loggers
from maxo.bot.api_client import MaxApiClient
from maxo.bot.defaults import BotDefaults
from maxo.bot.methods import (
    AddMembers,
    AnswerOnCallback,
    DeleteAdmin,
    DeleteChat,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditMessage,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
    GetMembers,
    GetMembership,
    GetMessageById,
    GetMessages,
    GetMyInfo,
    GetPinnedMessage,
    GetSubscriptions,
    GetUpdates,
    GetUploadUrl,
    GetVideoAttachmentDetails,
    LeaveChat,
    PinMessage,
    RemoveMember,
    SendAction,
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.state import (
    BotState,
    ClosedBotState,
    ConnectingBotState,
    EmptyBotState,
    RunningBotState,
)
from maxo.errors import MaxBotApiError
from maxo.serialization import create_retort_with_bot
from maxo.types import AttachmentPayload, MaxoType

_MethodResultT = TypeVar("_MethodResultT", bound=MaxoType)


class Bot(BaseAsyncClient):
    __slots__ = (
        "_defaults",
        "_json_dumps",
        "_json_loads",
        "_middleware",
        "_retort",
        "_state",
        "_token",
        "_warming_up",
    )

    def __init__(
        self,
        token: str,
        *,
        defaults: BotDefaults | None = None,
        warming_up: bool = True,
        middleware: list[AsyncMiddleware] | None = None,
        json_dumps: Callable[[Any], str] = json.dumps,
        json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
    ) -> None:
        self._defaults = defaults or BotDefaults()
        self._token = token
        self._warming_up = warming_up
        self._middleware = middleware
        self._json_dumps = json_dumps
        self._json_loads = json_loads

        self._retort = create_retort_with_bot(
            bot=self,
            defaults=self._defaults,
            warming_up=warming_up,
        )

        self._state: BotState = EmptyBotState()

    @property
    def state(self) -> BotState:
        return self._state

    @property
    def retort(self) -> Retort:
        return self._retort

    @property
    def defaults(self) -> BotDefaults:
        return self._defaults

    @property
    def token(self) -> str:
        return self._token

    @asynccontextmanager
    async def context(self, auto_close: bool = True) -> AsyncIterator[Self]:
        try:
            await self.start()
            yield self
        finally:
            if auto_close:
                await self.close()

    async def start(self) -> None:
        if self.state.started:
            return

        api_client = MaxApiClient(
            token=self._token,
            request_dumper=self._retort,
            response_loader=self._retort,
            middleware=self._middleware,
            json_dumps=self._json_dumps,
            json_loads=self._json_loads,
        )
        self._state = ConnectingBotState(api_client=api_client)

        info = await self.get_my_info()
        self._state = RunningBotState(info=info, api_client=api_client)

    async def close(self) -> None:
        if self.state.closed or not self.state.started:
            return

        await self.state.api_client.close()
        self._state = ClosedBotState()

    async def call_method(
        self,
        method: BaseMethod[ResponseType],
    ) -> ResponseType:
        return await self.state.api_client.call_method(method)

    async def silent_call_method(self, method: MaxoMethod[_MethodResultT]) -> None:
        try:
            await self.call_method(method)
        except MaxBotApiError as e:
            # In due to WebHook mechanism doesn't allow getting response for
            # requests called in answer to WebHook request.
            # Need to skip unsuccessful responses.
            # For debugging here is added logging.
            loggers.bot.error("Failed to make answer: %s: %s", e.__class__.__name__, e)

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def download(
        self,
        url: str | AttachmentPayload,
        destination: BinaryIO | pathlib.Path | str | None = None,
        timeout: float | ClientTimeout = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> BinaryIO | None:
        return await self.state.api_client.download(
            url=url,
            destination=destination,
            timeout=timeout,
            chunk_size=chunk_size,
            seek=seek,
        )

    # Bots

    edit_bot_info = bind_method(EditBotInfo)
    get_my_info = bind_method(GetMyInfo)

    # Chats

    add_members = bind_method(AddMembers)
    delete_admin = bind_method(DeleteAdmin)
    delete_chat = bind_method(DeleteChat)
    edit_chat = bind_method(EditChat)
    get_admins = bind_method(GetAdmins)
    get_chat = bind_method(GetChat)
    get_chat_by_link = bind_method(GetChatByLink)
    get_chats = bind_method(GetChats)
    get_members = bind_method(GetMembers)
    get_membership = bind_method(GetMembership)
    get_pinned_message = bind_method(GetPinnedMessage)
    leave_chat = bind_method(LeaveChat)
    pin_message = bind_method(PinMessage)
    remove_member = bind_method(RemoveMember)
    send_action = bind_method(SendAction)
    set_admins = bind_method(SetAdmins)
    unpin_message = bind_method(UnpinMessage)

    # Messages

    answer_on_callback = bind_method(AnswerOnCallback)
    delete_message = bind_method(DeleteMessage)
    edit_message = bind_method(EditMessage)
    get_message_by_id = bind_method(GetMessageById)
    get_messages = bind_method(GetMessages)
    get_video_attachment_details = bind_method(GetVideoAttachmentDetails)
    send_message = bind_method(SendMessage)

    # Subscriptions

    get_subscriptions = bind_method(GetSubscriptions)
    get_updates = bind_method(GetUpdates)
    subscribe = bind_method(Subscribe)
    unsubscribe = bind_method(Unsubscribe)

    # Uploads

    get_upload_url = bind_method(GetUploadUrl)
    upload_media = bind_method(UploadMedia)
