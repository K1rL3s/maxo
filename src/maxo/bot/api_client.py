"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/client/bot.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import io
import json
import pathlib
import ssl
from collections.abc import AsyncGenerator, Callable
from typing import Any, BinaryIO, Never

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiohttp.hdrs import AUTHORIZATION, USER_AGENT
from aiohttp.http import SERVER_SOFTWARE
from anyio import open_file
from unihttp.clients.aiohttp import AiohttpAsyncClient
from unihttp.http import HTTPResponse
from unihttp.method import BaseMethod
from unihttp.middlewares import AsyncMiddleware
from unihttp.serialize import RequestDumper, ResponseLoader

from maxo import loggers
from maxo.__meta__ import __version__
from maxo.bot.methods import AddMembers
from maxo.errors import (
    MaxBotApiError,
    MaxBotBadRequestError,
    MaxBotForbiddenError,
    MaxBotMethodNotAllowedError,
    MaxBotNotFoundError,
    MaxBotServiceUnavailableError,
    MaxBotTooManyRequestsError,
    MaxBotUnauthorizedError,
    MaxBotUnknownServerError,
    MaxBotUnsupportedMediaTypeError,
)
from maxo.types import AttachmentPayload


class MaxApiClient(AiohttpAsyncClient):
    def __init__(
        self,
        token: str,
        request_dumper: RequestDumper,
        response_loader: ResponseLoader,
        base_url: str = "https://platform-api2.max.ru/",
        middleware: list[AsyncMiddleware] | None = None,
        session: ClientSession | None = None,
        json_dumps: Callable[[Any], str] = json.dumps,
        json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
    ) -> None:
        self._token = token

        if session is None:
            cert = (pathlib.Path(__file__).parent / "russiantrustedca.pem").resolve()
            ssl_context = ssl.create_default_context()
            ssl_context.load_verify_locations(cafile=cert)
            connector = TCPConnector(ssl=ssl_context)
            session = ClientSession(connector=connector)

        if AUTHORIZATION not in session.headers:
            session.headers[AUTHORIZATION] = self._token
        if USER_AGENT not in session.headers:
            session.headers[USER_AGENT] = f"{SERVER_SOFTWARE} maxo/{__version__}"

        super().__init__(
            base_url=base_url,
            request_dumper=request_dumper,
            response_loader=response_loader,
            middleware=middleware,
            session=session,
            json_dumps=json_dumps,
            json_loads=json_loads,
        )

    def handle_error(self, response: HTTPResponse, method: BaseMethod[Any]) -> Never:
        # ruff: noqa: PLR2004
        data = response.data
        if isinstance(data, dict):
            code: str = data.get("code") or data.get("error_code", "")
            error: str = data.get("error") or data.get("error_data", "")
            message: str = data.get("message", "")
        else:
            code = ""
            error = ""
            message = ""

        if response.status_code == 400:
            raise MaxBotBadRequestError(code, error, message, data)
        if response.status_code == 401:
            raise MaxBotUnauthorizedError(code, error, message, data)
        if response.status_code == 403:
            raise MaxBotForbiddenError(code, error, message, data)
        if response.status_code == 404:
            raise MaxBotNotFoundError(code, error, message, data)
        if response.status_code == 405:
            raise MaxBotMethodNotAllowedError(code, error, message, data)
        if response.status_code == 415:
            raise MaxBotUnsupportedMediaTypeError(code, error, message, data)
        if response.status_code == 429:
            raise MaxBotTooManyRequestsError(code, error, message, data)
        if response.status_code == 500:
            raise MaxBotUnknownServerError(code, error, message, data)
        if response.status_code == 503:
            raise MaxBotServiceUnavailableError(code, error, message, data)
        raise MaxBotApiError(code, error, message, data)

    def validate_response(
        self,
        response: HTTPResponse,
        method: BaseMethod[Any],
    ) -> None:
        if (
            response.ok
            and isinstance(response.data, dict)
            and (
                response.data.get("error_code")
                or response.data.get("success", None) is False
            )
        ):
            if isinstance(method, AddMembers):
                # При ошибке добавления юзера апи возвращает success=false и статус 200,
                # и даёт подробную инфу в ModifyMembersResult.
                # Из-за этого для нормальной работы метода нужно не патчить его статус
                return
            loggers.bot_session.warning(
                "Patch the status code from %d to 400 due to an error on the MAX API",
                response.status_code,
            )
            response.status_code = 400

    async def download(
        self,
        url: str | AttachmentPayload,
        destination: BinaryIO | pathlib.Path | str | None = None,
        timeout: float | ClientTimeout = 30,
        chunk_size: int = 65536,
        seek: bool = True,
    ) -> BinaryIO | None:
        if isinstance(url, AttachmentPayload):
            url = url.url

        return await self._download_file(
            url,
            destination=destination,
            timeout=timeout,
            chunk_size=chunk_size,
            seek=seek,
        )

    async def _download_file(
        self,
        url: str,
        destination: BinaryIO | pathlib.Path | str | None,
        timeout: float | ClientTimeout,
        chunk_size: int,
        seek: bool,
    ) -> BinaryIO | None:
        if destination is None:
            destination = io.BytesIO()

        stream = self._stream_content(
            url=url,
            timeout=timeout,
            chunk_size=chunk_size,
            raise_for_status=True,
        )

        if isinstance(destination, (str, pathlib.Path)):
            await self.__download_file(destination=destination, stream=stream)
            return None
        return await self.__download_file_binary_io(
            destination=destination,
            seek=seek,
            stream=stream,
        )

    async def _stream_content(
        self,
        url: str,
        headers: dict[str, Any] | None = None,
        timeout: float | ClientTimeout = 30,
        chunk_size: int = 65536,
        raise_for_status: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        if not isinstance(timeout, ClientTimeout):
            timeout = ClientTimeout(total=timeout)

        async with self._session.get(
            url,
            timeout=timeout,
            headers=headers,
            raise_for_status=raise_for_status,
        ) as resp:
            async for chunk in resp.content.iter_chunked(chunk_size):
                yield chunk

    @classmethod
    async def __download_file(
        cls,
        destination: str | pathlib.Path,
        stream: AsyncGenerator[bytes, None],
    ) -> None:
        async with await open_file(destination, "wb") as f:
            async for chunk in stream:
                await f.write(chunk)

    @classmethod
    async def __download_file_binary_io(
        cls,
        destination: BinaryIO,
        seek: bool,
        stream: AsyncGenerator[bytes, None],
    ) -> BinaryIO:
        async for chunk in stream:
            destination.write(chunk)
            destination.flush()
        if seek is True:
            destination.seek(0)
        return destination
