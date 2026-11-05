from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientResponseError, ClientSession, web
from aiohttp.pytest_plugin import AiohttpServer

from examples import swagger_watcher

PAGE = """<html><head><script>var bundle = "abc";</script></head><body>
<nav>Меню</nav>
<main><h1>User</h1><p>Объект <code>User</code></p>
<div class="api-param"><span>user_id</span><svg><path d="M1"/></svg>
<span>integer &lt;int64&gt;</span></div><script>{"x": 1}</script></main>
<footer>Подвал</footer></body></html>"""


def settings(tmp_path: Path) -> swagger_watcher.Settings:
    state = tmp_path / "state.json"
    return swagger_watcher.Settings(
        max_recipient=None,
        telegram_recipient=None,
        interval=1,
        state_path=state,
        pending_path=tmp_path / ".state.json.delivery.json",
    )


def test_extract_page_text() -> None:
    assert swagger_watcher.extract_page_text(PAGE) == [
        "User",
        "Объект User",
        "user_id",
        "integer <int64>",
    ]


def test_extract_page_text_without_main() -> None:
    with pytest.raises(RuntimeError, match="<main>"):
        swagger_watcher.extract_page_text("<html><body>Пусто</body></html>")


def test_select_page_paths() -> None:
    index: list[swagger_watcher.JsonValue] = [
        {"permalink": f"https://dev.max.ru/docs-api/objects/Type{number}/"}
        for number in range(40)
    ]
    index += [
        {"permalink": "https://dev.max.ru/docs-api/methods/GET/me/"},
        {"permalink": "https://dev.max.ru/docs-api/use-cases/webhooks/"},
        {"title": "без ссылки"},
    ]

    paths = swagger_watcher.select_page_paths(index)

    assert len(paths) == 41
    assert "/docs-api/methods/GET/me/" in paths
    assert "/docs-api/use-cases/webhooks/" not in paths


def test_select_page_paths_too_few() -> None:
    with pytest.raises(RuntimeError, match="ожидалось не меньше 40"):
        swagger_watcher.select_page_paths(
            [{"permalink": "https://dev.max.ru/docs-api/methods/GET/me/"}],
        )


async def test_check_for_update_detects_page_change(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages: list[swagger_watcher.JsonObject] = [
        {"/docs-api/objects/User/": ["User", "user_id"]},
        {"/docs-api/objects/User/": ["User", "user_id"]},
        {
            "/docs-api/objects/User/": ["User", "user_id", "avatar_url"],
            "/docs-api/objects/Chat/": ["Chat"],
        },
    ]
    monkeypatch.setattr(
        swagger_watcher,
        "fetch_site_pages",
        AsyncMock(side_effect=pages),
    )
    publish = AsyncMock()
    monkeypatch.setattr(swagger_watcher, "publish_update", publish)
    current = settings(tmp_path)
    session = MagicMock()

    await swagger_watcher.check_for_update(session, current)
    publish.assert_not_awaited()
    assert current.state_path.exists()

    await swagger_watcher.check_for_update(session, current)
    publish.assert_not_awaited()

    await swagger_watcher.check_for_update(session, current)
    publish.assert_awaited_once()
    assert publish.await_args is not None
    _, diff, message, _ = publish.await_args.args
    assert message.endswith("Страницы: +1 / -0 / ~1")
    assert '+    "avatar_url"' in diff
    assert "avatar_url" in current.state_path.read_text(encoding="utf-8")


def site_app(missing: str = "") -> web.Application:
    index = [
        {"permalink": f"https://dev.max.ru/docs-api/objects/Type{number}/"}
        for number in range(40)
    ]
    index.append({"permalink": "https://dev.max.ru/docs-api/use-cases/webhooks/"})

    async def index_json(_: web.Request) -> web.Response:
        return web.json_response(index)

    async def page(request: web.Request) -> web.Response:
        name = request.match_info["name"]
        if name == missing:
            raise web.HTTPNotFound
        html = f"<main><h1>{name}</h1></main>"
        return web.Response(text=html, content_type="text/html")

    app = web.Application()
    app.router.add_get("/index.json", index_json)
    app.router.add_get("/docs-api/objects/{name}/", page)
    return app


async def fetch_from(
    server: AiohttpServer,
    app: web.Application,
    monkeypatch: pytest.MonkeyPatch,
) -> swagger_watcher.JsonObject:
    site = str((await server(app)).make_url("/")).rstrip("/")
    monkeypatch.setattr(swagger_watcher, "SITE_URL", site)
    monkeypatch.setattr(swagger_watcher, "INDEX_URL", f"{site}/index.json")
    monkeypatch.setattr(swagger_watcher, "PAGE_DELAY", 0)
    async with ClientSession() as session:
        return await swagger_watcher.fetch_site_pages(session)


async def test_fetch_site_pages(
    aiohttp_server: AiohttpServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages = await fetch_from(aiohttp_server, site_app(), monkeypatch)

    assert len(pages) == 40
    assert pages["/docs-api/objects/Type7/"] == ["Type7"]


async def test_fetch_site_pages_fails_on_http_error(
    aiohttp_server: AiohttpServer,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ClientResponseError) as error:
        await fetch_from(aiohttp_server, site_app(missing="Type7"), monkeypatch)

    assert error.value.status == 404
