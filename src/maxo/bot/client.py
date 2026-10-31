import json
import pathlib
import ssl
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from unihttp.middlewares import AsyncMiddleware

from maxo.serialization import get_retort

if TYPE_CHECKING:
    from aiohttp import ClientSession, ClientTimeout
    from unihttp.clients.aiohttp import AiohttpAsyncClient

CA_CERT_PATH = (pathlib.Path(__file__).parent / "russiantrustedca.pem").resolve()
BASE_URL = "https://platform-api2.max.ru/"
_DEFAULT_LIMIT = 100  # same as aiohttp `TCPConnector`


def build_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=CA_CERT_PATH)
    return context


def default_media_client(
    *,
    ssl_context: ssl.SSLContext | None = None,
    limit: int = _DEFAULT_LIMIT,
    timeout: "ClientTimeout | None" = None,
    session: "ClientSession | None" = None,
) -> "AiohttpAsyncClient":
    """
    Клиент файловых хостов: без общего таймаута, загрузка 2 ГиБ идёт минутами.

    Зависший ответ всё равно ловит `sock_read`.
    """
    from aiohttp import ClientTimeout  # noqa: PLC0415

    if session is None and timeout is None:
        timeout = ClientTimeout(total=None, sock_connect=30, sock_read=300)
    return default_client(
        ssl_context=ssl_context,
        limit=limit,
        timeout=timeout,
        session=session,
    )


def default_client(
    *,
    base_url: str = BASE_URL,
    middleware: list[AsyncMiddleware] | None = None,
    ssl_context: ssl.SSLContext | None = None,
    json_dumps: Callable[[Any], str] = json.dumps,
    json_loads: Callable[[str | bytes | bytearray], Any] = json.loads,
    limit: int = _DEFAULT_LIMIT,
    timeout: "ClientTimeout | None" = None,
    session: "ClientSession | None" = None,
) -> "AiohttpAsyncClient":
    """
    Aiohttp-клиент, доверяющий корневому сертификату Минцифры.

    `ssl_context`, `limit` и `timeout` настраивают создаваемую здесь сессию,
    поэтому вместе со своей `session` они дают `TypeError`.
    """
    # Lazy: importing aiohttp costs ~0.4s, keep it out of `import maxo`
    from aiohttp import ClientSession, TCPConnector  # noqa: PLC0415
    from unihttp.clients.aiohttp import AiohttpAsyncClient  # noqa: PLC0415

    if session is not None:
        if ssl_context is not None or limit != _DEFAULT_LIMIT or timeout is not None:
            msg = "`ssl_context`, `limit` and `timeout` can't be used with `session`"
            raise TypeError(msg)
    else:
        session = ClientSession(
            connector=TCPConnector(
                ssl=ssl_context or build_ssl_context(),
                limit=limit,
            ),
            timeout=timeout,  # None -> aiohttp default
        )
    return AiohttpAsyncClient(
        base_url=base_url,
        request_dumper=get_retort(),
        response_loader=get_retort(),
        middleware=middleware or [],
        session=session,
        json_dumps=json_dumps,
        json_loads=json_loads,
    )
