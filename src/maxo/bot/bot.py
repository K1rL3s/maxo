import asyncio
import io
import json
import pathlib
from collections.abc import AsyncIterator, Iterable, Sequence
from contextlib import asynccontextmanager
from types import TracebackType
from typing import TYPE_CHECKING, BinaryIO, NoReturn, Self

from unihttp.bind_method import bind_method
from unihttp.clients.base import BaseAsyncClient
from unihttp.method import BaseMethod, ResponseType, StreamMethod
from unihttp.middlewares import AsyncMiddleware

from maxo.bot.client import _file_host_session, default_client
from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import (  # type: ignore[deprecated]
    AddMembers,
    AnswerOnCallback,
    DeleteAdmins,
    DeleteChat,
    DeleteComment,
    DeleteMessage,
    EditBotInfo,
    EditChat,
    EditComment,
    EditMessage,
    EditMyCommands,
    GetAdmins,
    GetChat,
    GetChatByLink,
    GetChats,
    GetCommentById,
    GetComments,
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
    SendComment,
    SendMessage,
    SetAdmins,
    Subscribe,
    UnpinMessage,
    Unsubscribe,
    UploadMedia,
)
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    AuthMiddleware,
    NetworkErrorMiddleware,
    UserAgentMiddleware,
)
from maxo.bot.upload import UploadConfig, resumable_upload
from maxo.bot.warming_up import warm_up
from maxo.errors import UnsubscribeError
from maxo.serialization import get_retort
from maxo.types import AttachmentPayload, BotInfo, ClearSubscriptionsResult
from maxo.types.binding import bind_bot
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

if TYPE_CHECKING:
    from aiohttp import ClientTimeout


class Bot(BaseAsyncClient):  # BaseAsyncClient for mypy
    def __init__(
        self,
        token: str,
        *,
        defaults: BotDefaults | None = None,
        warming_up: bool = True,
        client: BaseAsyncClient | None = None,
        upload_config: UploadConfig | None = None,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> None:
        self._defaults = defaults or BotDefaults()
        self._token = token
        self._upload_config = (
            upload_config if upload_config is not None else UploadConfig()
        )

        self.middleware: list[AsyncMiddleware] = [
            *(middleware or ()),
            AuthMiddleware(self._token),
            UserAgentMiddleware(),
            AttachmentNotReadyRetryMiddleware(
                max_retries=self._upload_config.not_ready_max_retries,
                backoff_config=self._upload_config.not_ready_backoff,
            ),
            NetworkErrorMiddleware(),
        ]
        self._client = client
        self._owns_client = client is None

        if warming_up:
            warm_up()

        self._info: BotInfo | None = None
        self._me_lock = asyncio.Lock()

    @property
    def client(self) -> BaseAsyncClient:
        if self._client is None:
            self._client = default_client()
        return self._client

    @property
    def upload_config(self) -> UploadConfig:
        return self._upload_config

    @property
    def defaults(self) -> BotDefaults:
        return self._defaults

    @property
    def token(self) -> str:
        return self._token

    @asynccontextmanager
    async def context(self, auto_close: bool = True) -> AsyncIterator[Self]:
        try:
            await self.me()
            yield self
        finally:
            if auto_close:
                await self.close()

    async def __aenter__(self) -> Self:
        try:
            await self.me()
        except BaseException:
            await self.close()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def me(self) -> BotInfo:
        if self._info is None:
            async with self._me_lock:
                if self._info is None:
                    return await self.get_my_info()
        return self._info

    start = me

    async def get_my_info(self) -> BotInfo:
        self._info = await self.call_method(GetMyInfo())
        return self._info

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            client, self._client = self._client, None
            await client.close()

    async def call_method(  # for unihttp bind_method
        self,
        method: BaseMethod[ResponseType],
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> ResponseType:
        method = apply_defaults(method, self._defaults)
        result = await self.client.call_method(
            method,
            middleware=[*(middleware or ()), *self.middleware],
        )
        return bind_bot(result, self)

    async def call_method_stream(
        self,
        method: StreamMethod,
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> NoReturn:
        msg = "Bot не стримит ответы API, скачивайте файлы через bot.download()"
        raise NotImplementedError(msg)

    # Bots
    edit_bot_info = bind_method(EditBotInfo)
    edit_my_commands = bind_method(EditMyCommands)

    # Chats
    add_members = bind_method(AddMembers)
    delete_admins = bind_method(DeleteAdmins)
    delete_admin = delete_admins
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

    # Comments

    delete_comment = bind_method(DeleteComment)
    edit_comment = bind_method(EditComment)
    get_comment_by_id = bind_method(GetCommentById)
    get_comments = bind_method(GetComments)
    send_comment = bind_method(SendComment)

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

    async def clear_subscriptions(
        self,
        active_urls: str | Iterable[str] | None = None,
    ) -> ClearSubscriptionsResult:
        """
        Удаляет все WebHook-подписки, кроме активных.

        Args:
            active_urls: URL подписок, которые нужно сохранить: одна строка или
                итерируемый набор строк. Одновременно может работать несколько
                подписок (бот, статистика и т.п.). Сравнение точное, поэтому
                URL должны совпадать с тем, что вернул `get_subscriptions`.
                Если не передан, удаляются все подписки.

        Returns:
            Удалённые и сохранённые подписки.

        Raises:
            BaseExceptionGroup: Если хотя бы одну подписку удалить не удалось.
                Все запросы при этом доводятся до конца, а в группу попадают
                ошибки по каждой неудачной попытке: обычные - обёрнутыми в
                `UnsubscribeError` с URL, `BaseException` - как есть. Если
                `BaseException` не было, группа сужается до `ExceptionGroup`.

        """
        if active_urls is None:
            urls_to_keep: frozenset[str] = frozenset()
        elif isinstance(active_urls, str):
            urls_to_keep = frozenset((active_urls,))
        else:
            urls_to_keep = frozenset(active_urls)

        subscriptions = (await self.get_subscriptions()).subscriptions
        to_remove = [
            subscription
            for subscription in subscriptions
            if subscription.url not in urls_to_keep
        ]
        kept = [
            subscription
            for subscription in subscriptions
            if subscription.url in urls_to_keep
        ]

        results = await asyncio.gather(
            *(self.unsubscribe(url=subscription.url) for subscription in to_remove),
            return_exceptions=True,
        )

        errors: list[BaseException] = []
        for subscription, result in zip(to_remove, results, strict=True):
            if not isinstance(result, BaseException):
                continue
            if not isinstance(result, Exception):
                errors.append(result)
                continue
            error = UnsubscribeError(url=subscription.url, error=result)
            error.__cause__ = result
            errors.append(error)

        if errors:
            raise BaseExceptionGroup("Не удалось удалить WebHook-подписки", errors)

        return ClearSubscriptionsResult(removed=to_remove, kept=kept)

    # Uploads
    get_upload_url = bind_method(GetUploadUrl)
    upload_media = bind_method(UploadMedia)

    async def upload_media_resumable(
        self,
        upload_url: str,
        file: InputFile,
        size: int | None = None,
    ) -> UploadMediaResult | None:
        """
        Загружает медиа по `upload_url` частями.

        `size` - заранее известный размер файла, чтобы не делать лишний `stat`.
        """
        # One connection: the upload session lives on it
        async with _file_host_session(limit=1) as session:
            return await resumable_upload(
                url=upload_url,
                file=file,
                session=session,
                response_loader=get_retort(),
                json_loads=json.loads,
                config=self._upload_config,
                size=size,
            )

    async def download(
        self,
        url: str | AttachmentPayload,
        destination: BinaryIO | pathlib.Path | str | None = None,
        timeout: "float | ClientTimeout" = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> BinaryIO | None:
        """
        Скачивает вложение в `destination`: файл по пути или `BinaryIO`.

        Без `destination` - в `BytesIO`. Для пути возвращает `None`.
        """
        from aiohttp import ClientTimeout  # noqa: PLC0415
        from anyio import open_file  # noqa: PLC0415

        if isinstance(url, AttachmentPayload):
            url = url.url
        if not isinstance(timeout, ClientTimeout):
            timeout = ClientTimeout(total=timeout)

        async with (
            _file_host_session() as session,
            session.get(url, timeout=timeout, raise_for_status=True) as response,
        ):
            chunks = response.content.iter_chunked(chunk_size)
            if isinstance(destination, str | pathlib.Path):
                async with await open_file(destination, "wb") as file:
                    async for chunk in chunks:
                        await file.write(chunk)
                return None

            if destination is None:
                destination = io.BytesIO()
            async for chunk in chunks:
                destination.write(chunk)
                destination.flush()
        if seek:
            destination.seek(0)
        return destination
