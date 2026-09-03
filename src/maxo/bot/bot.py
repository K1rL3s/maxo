import pathlib
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing, asynccontextmanager
from typing import Self
from urllib.parse import quote

from anyio import open_file
from unihttp.bind_method import bind_method
from unihttp.clients.base import BaseAsyncClient
from unihttp.http.response import HTTPResponse
from unihttp.http.stream import AsyncChunkStream
from unihttp.method import BaseMethod, ResponseType, StreamMethod
from unihttp.middlewares import AsyncMiddleware

from maxo.bot.client import default_client
from maxo.bot.defaults import BotDefaults, apply_defaults
from maxo.bot.methods import (
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
from maxo.bot.methods.download import Download
from maxo.bot.methods.upload.chunk_upload import UploadResponseBody, _ChunkUpload
from maxo.bot.middlewares import (
    AttachmentNotReadyRetryMiddleware,
    AuthMiddleware,
    ChunkUploadRetryMiddleware,
    NetworkErrorMiddleware,
)
from maxo.bot.upload import UploadConfig
from maxo.bot.warming_up import warm_up
from maxo.errors import MaxBotApiError
from maxo.errors.api import raise_api_error
from maxo.errors.state import StateError
from maxo.serialization import get_retort
from maxo.types import AttachmentPayload, BotInfo
from maxo.types.binding import bind_bot
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import InputFile

_CLIENT_ERROR_STATUS = 400
_DEFAULT_CHUNK_SIZE = 65536


class Bot(BaseAsyncClient):  # BaseAsyncClient for mypy
    def __init__(
        self,
        token: str,
        *,
        defaults: BotDefaults | None = None,
        upload_config: UploadConfig | None = None,
        warming_up: bool = True,
        client: BaseAsyncClient | None = None,
        middlewares: Sequence[AsyncMiddleware] = (),
    ) -> None:
        self._defaults = defaults or BotDefaults()
        self._token = token
        self._upload_config = (
            upload_config if upload_config is not None else UploadConfig()
        )

        self.middleware: list[AsyncMiddleware] = [
            *middlewares,
            AuthMiddleware(self._token),
            AttachmentNotReadyRetryMiddleware(
                max_retries=self._upload_config.not_ready_max_retries,
                backoff_config=self._upload_config.not_ready_backoff,
            ),
            NetworkErrorMiddleware(),
        ]
        self._client = client

        self._owns_client = client is None
        self._closed = False

        if warming_up:
            warm_up()

        self._info: BotInfo | None = None

    @property
    def client(self) -> BaseAsyncClient:
        if self._client is None:
            self._client = default_client()
        return self._client

    @property
    def info(self) -> BotInfo:
        if self._info is None:
            raise StateError("Bot info is not resolved yet")
        return self._info

    @property
    def started(self) -> bool:
        return self._info is not None

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def defaults(self) -> BotDefaults:
        return self._defaults

    @property
    def upload_config(self) -> UploadConfig:
        return self._upload_config

    @property
    def token(self) -> str:
        return self._token

    @asynccontextmanager
    async def context(
        self,
        auto_close: bool = True,
        get_my_info: bool = True,
    ) -> AsyncIterator[Self]:
        try:
            if get_my_info:
                await self.get_my_info()
            yield self
        finally:
            if auto_close:
                await self.close()

    async def get_my_info(self) -> BotInfo:
        info = await self.client.call_method(GetMyInfo(), middleware=self.middleware)
        self._info = bind_bot(info, self)
        return self._info

    async def close(self) -> None:
        if self._closed or self._client is None:
            return
        self._closed = True

        if self._owns_client:
            await self._client.close()

    async def call_method(  # for unihttp bind_method
        self,
        method: BaseMethod[ResponseType],
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> ResponseType:
        method = apply_defaults(method, self._defaults)
        result = await self.client.call_method(
            method,
            # Middleware вызова идут первыми: так они получают ошибки maxo,
            # а не сырые исключения unihttp.
            middleware=[*(middleware or ()), *self.middleware],
        )
        return bind_bot(result, self)

    async def call_method_stream(  # for unihttp bind_method
        self,
        method: StreamMethod,
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> HTTPResponse[AsyncChunkStream]:
        return await self.client.call_method_stream(
            method,
            middleware=[*(middleware or ()), *self.middleware],
        )

    @asynccontextmanager
    async def download_stream(
        self,
        url: str | AttachmentPayload,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> AsyncIterator[AsyncIterator[bytes]]:
        """
        Отдаёт вложение чанками.

        Соединение освобождается на выходе из `async with`, в том числе
        при прерванном цикле.
        """
        if isinstance(url, AttachmentPayload):
            url = url.url

        response = await self.call_method_stream(
            Download(url=url, __chunk_size__=chunk_size),
        )
        async with response.data as stream:
            yield stream

    async def download(
        self,
        url: str | AttachmentPayload,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> bytes:
        """
        Скачивает вложение целиком в память.

        Для больших файлов: `download_to()` или `download_stream()`.
        """
        buffer = bytearray()
        async with self.download_stream(url, chunk_size=chunk_size) as chunks:
            async for chunk in chunks:
                buffer += chunk
        return bytes(buffer)

    async def download_to(
        self,
        url: str | AttachmentPayload,
        path: pathlib.Path | str,
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
    ) -> None:
        """Скачивает вложение в файл. Каталог должен существовать."""
        async with (
            self.download_stream(url, chunk_size=chunk_size) as chunks,
            await open_file(path, "wb") as file,
        ):
            async for chunk in chunks:
                await file.write(chunk)

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
        config = self.upload_config

        if size is None:
            size = await file.size()
        if size <= 0:
            msg = "Нельзя загрузить пустой файл"
            raise ValueError(msg)

        encoded_name = quote(file.file_name, safe="")
        disposition = f'attachment; filename="{encoded_name}"'

        offset = 0
        final_body: UploadResponseBody = b""
        # aclosing: при ошибке `async for` не закрывает генератор, а у
        # `FSInputFile.stream` внутри него остаётся открытый файл.
        async with aclosing(file.stream(config.chunk_size)) as chunks:
            async for chunk in chunks:
                end = offset + len(chunk) - 1
                headers: dict[str, str] = {
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": disposition,
                    "Content-Range": f"bytes {offset}-{end}/{size}",
                }
                response = await self.call_method(
                    _ChunkUpload(url=upload_url, chunk=chunk, headers=headers),
                    middleware=[
                        ChunkUploadRetryMiddleware(
                            max_retries=config.chunk_retries,
                            backoff_config=config.chunk_backoff,
                        ),
                    ],
                )
                body = response.data
                if response.status_code < _CLIENT_ERROR_STATUS:
                    final_body = body
                elif isinstance(body, dict):
                    raise_api_error(response.status_code, body)
                else:
                    raise MaxBotApiError(
                        code="",
                        error=f"upload failed with status {response.status_code}",
                        message=body.decode("utf-8", "replace")
                        if isinstance(body, bytes)
                        else str(body or ""),
                        raw_data=body,
                    )

                offset += len(chunk)

        if offset != size:
            # Файл изменился между замером размера и чтением
            msg = f"Размер файла изменился во время загрузки: {size} -> {offset} байт"
            raise ValueError(msg)

        if not isinstance(final_body, dict):
            return None
        return get_retort().load(final_body, UploadMediaResult)

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

    # Uploads
    get_upload_url = bind_method(GetUploadUrl)
    upload_media = bind_method(UploadMedia)
