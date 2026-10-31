import asyncio
import io
import secrets
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from contextlib import (
    AbstractContextManager,
    aclosing,
    asynccontextmanager,
    nullcontext,
)
from pathlib import Path
from typing import BinaryIO
from urllib.parse import quote

from anyio import Path as AsyncPath, open_file
from unihttp.clients.base import BaseAsyncClient
from unihttp.http import UploadFile
from unihttp.http.response import HTTPResponse
from unihttp.http.stream import AsyncChunkStream
from unihttp.method import BaseMethod, ResponseType, StreamMethod
from unihttp.middlewares import AsyncMiddleware

from maxo.bot.client import default_media_client
from maxo.bot.methods.download import Download
from maxo.bot.methods.upload.chunk_upload import ChunkUpload, UploadResponseBody
from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.bot.middlewares import (
    ChunkUploadRetryMiddleware,
    NetworkErrorMiddleware,
    UserAgentMiddleware,
)
from maxo.bot.middlewares.network_error import translate_network_errors
from maxo.bot.upload import UploadConfig
from maxo.serialization import get_retort
from maxo.types import AttachmentPayload
from maxo.types.upload_media_result import UploadMediaResult
from maxo.utils.upload_media import FSInputFile, InputFile

DEFAULT_DOWNLOAD_CHUNK_SIZE = 65536


class Media:
    """
    Клиент файловых хостов MAX, доступен как `bot.media`.

    Свои HTTP-клиент и middleware, без токена и без вызовов API.
    Переданный `client` не закрывается.
    """

    def __init__(
        self,
        client: BaseAsyncClient | None = None,
        config: UploadConfig | None = None,
    ) -> None:
        self.config = config if config is not None else UploadConfig()
        self._client = client
        self._owns_client = client is None
        self.middleware: list[AsyncMiddleware] = [
            UserAgentMiddleware(),
            NetworkErrorMiddleware(),
        ]

    @property
    def client(self) -> BaseAsyncClient:
        if self._client is None:
            self._client = default_media_client()
        return self._client

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            client, self._client = self._client, None
            await client.close()

    async def call_method(
        self,
        method: BaseMethod[ResponseType],
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> ResponseType:
        # Middleware вызова идут первыми: так они получают ошибки maxo,
        # а не сырые исключения unihttp.
        return await self.client.call_method(
            method,
            middleware=[*(middleware or ()), *self.middleware],
        )

    async def call_method_stream(
        self,
        method: StreamMethod,
        *,
        middleware: Sequence[AsyncMiddleware] | None = None,
    ) -> HTTPResponse[AsyncChunkStream]:
        return await self.client.call_method_stream(
            method,
            middleware=[*(middleware or ()), *self.middleware],
        )

    async def upload(
        self,
        url: str,
        file: InputFile,
        size: int | None = None,
    ) -> UploadMediaResult | None:
        """
        Загружает файл по `url` из `get_upload_url`.

        Частями или одним запросом - по `config`. `None`, если хост не вернул
        токен (тогда он есть в ответе `get_upload_url`).
        """
        if size is None:
            size = await file.size()
        if size <= 0:
            msg = "Нельзя загрузить пустой файл"
            raise ValueError(msg)

        if self.config.should_use_resumable(file.type, size):
            return await self._upload_resumable(url, file, size)

        source: AbstractContextManager[bytes | BinaryIO]
        if isinstance(file, FSInputFile):
            # Streamed, not read into memory
            source = await asyncio.to_thread(Path(file.path).open, "rb")
        else:
            source = nullcontext(await file.read())
        with source as content:
            return await self.call_method(
                UploadMedia(
                    upload_url=url,
                    file=UploadFile(file=content, filename=file.file_name),
                ),
            )

    async def _upload_resumable(
        self,
        upload_url: str,
        file: InputFile,
        size: int,
    ) -> UploadMediaResult | None:
        """Загружает видео или аудио по `upload_url` частями."""
        config = self.config

        encoded_name = quote(file.file_name, safe="")
        disposition = f'attachment; filename="{encoded_name}"'

        offset = 0
        final_body: UploadResponseBody = b""
        retry = ChunkUploadRetryMiddleware(
            max_retries=config.chunk_retries,
            backoff_config=config.chunk_backoff,
        )
        # aclosing: при ошибке `async for` не закрывает генератор, а у
        # `FSInputFile.stream` внутри него остаётся открытый файл.
        async with aclosing(file.stream(config.chunk_size)) as chunks:
            async for chunk in chunks:
                end = offset + len(chunk) - 1
                final_body = await self.call_method(
                    ChunkUpload(
                        upload_url=upload_url,
                        content_range=f"bytes {offset}-{end}/{size}",
                        content_disposition=disposition,
                        chunk=chunk,
                    ),
                    middleware=[retry],
                )
                offset += len(chunk)

        if offset != size:
            # Файл изменился между замером размера и чтением
            msg = f"Размер файла изменился во время загрузки: {size} -> {offset} байт"
            raise ValueError(msg)

        if not isinstance(final_body, dict):
            return None
        return get_retort().load(final_body, UploadMediaResult)

    @asynccontextmanager
    async def download_stream(
        self,
        url: str | AttachmentPayload,
        chunk_size: int = DEFAULT_DOWNLOAD_CHUNK_SIZE,
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
        async with (
            response.data as stream,
            aclosing(_translate_chunks(stream)) as chunks,
        ):
            yield chunks

    async def download(
        self,
        url: str | AttachmentPayload,
        chunk_size: int = DEFAULT_DOWNLOAD_CHUNK_SIZE,
    ) -> bytes:
        """
        Скачивает вложение целиком в память.

        Для больших файлов: `download_to()` или `download_stream()`.
        """
        buffer = io.BytesIO()
        async with self.download_stream(url, chunk_size=chunk_size) as chunks:
            async for chunk in chunks:
                buffer.write(chunk)
        return buffer.getvalue()

    async def download_to(
        self,
        url: str | AttachmentPayload,
        path: Path | str,
        chunk_size: int = DEFAULT_DOWNLOAD_CHUNK_SIZE,
    ) -> None:
        """
        Скачивает вложение в файл. Каталог должен существовать.

        Пишет во временный `<path>.<random>.part` и переименовывает его в конце:
        при ошибке `path` не тронут, а `.part` удаляется.
        """
        target = AsyncPath(path)
        # Unique name: parallel downloads to one path don't share a `.part`
        part = target.with_name(f"{target.name}.{secrets.token_hex(4)}.part")
        try:
            async with (
                self.download_stream(url, chunk_size=chunk_size) as chunks,
                await open_file(part, "wb") as file,
            ):
                async for chunk in chunks:
                    await file.write(chunk)
        except BaseException:
            await part.unlink(missing_ok=True)
            raise
        await part.replace(target)


async def _translate_chunks(stream: AsyncIterator[bytes]) -> AsyncGenerator[bytes]:
    # Only reading: errors from the caller's `async with` body stay as is
    with translate_network_errors():
        async for chunk in stream:
            yield chunk
