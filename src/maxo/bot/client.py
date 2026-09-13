import json
import pathlib
import ssl
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from unihttp.middlewares import AsyncMiddleware
from unihttp.serialize import RequestDumper, ResponseLoader

from maxo.serialization import get_retort

if TYPE_CHECKING:
    from aiohttp import ClientSession, ClientTimeout
    from unihttp.clients.aiohttp import AiohttpAsyncClient

CA_CERT_PATH = (pathlib.Path(__file__).parent / "russiantrustedca.pem").resolve()
BASE_URL = "https://platform-api2.max.ru/"


def build_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=CA_CERT_PATH)
    return context


def default_client(
    *,
    request_dumper: RequestDumper | None = None,
    response_loader: ResponseLoader | None = None,
    base_url: str = BASE_URL,
    middleware: list[AsyncMiddleware] | None = None,
    ssl_context: ssl.SSLContext | None = None,
    json_dumps: Callable[[Any], str] = json.dumps,
    json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
    limit: int | None = None,
    timeout: "ClientTimeout | None" = None,
    session: "ClientSession | None" = None,
) -> "AiohttpAsyncClient":
    # Отложенный импорт: `aiohttp` нужен только тому, кто берет клиент по
    # умолчанию. `Bot(client=...)` с другой реализацией `BaseAsyncClient`
    # его не тянет, как и импорт самого `maxo`.
    from aiohttp import ClientSession, TCPConnector  # noqa: PLC0415
    from unihttp.clients.aiohttp import AiohttpAsyncClient  # noqa: PLC0415

    if request_dumper is None:
        request_dumper = get_retort()
    if response_loader is None:
        response_loader = get_retort()

    if session is None:
        if ssl_context is None:
            ssl_context = build_ssl_context()

        connector = (
            TCPConnector(ssl=ssl_context)
            if limit is None
            else TCPConnector(ssl=ssl_context, limit=limit)
        )
        session = (
            ClientSession(connector=connector)
            if timeout is None
            else ClientSession(connector=connector, timeout=timeout)
        )
    return AiohttpAsyncClient(
        base_url=base_url,
        request_dumper=request_dumper,
        response_loader=response_loader,
        middleware=middleware or [],
        session=session,
        json_dumps=json_dumps,
        json_loads=json_loads,
    )
