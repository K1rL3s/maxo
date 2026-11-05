import argparse
import asyncio
import importlib
import importlib.util
import inspect
import os.path
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from aiohttp import web

from maxo.dialogs.tools.preview import render_preview_content
from maxo.dialogs.tools.transitions import render_transitions
from maxo.routing.interfaces import BaseRouter


def removesuffix(s: str, suffix: str) -> str:
    if s.endswith(suffix):
        return s[: -len(suffix)]
    return s


class Renderer:
    def __init__(self, app_module: str, dialogs_router: str) -> None:
        self.app_module = app_module
        self.dialogs_router = dialogs_router

    async def _get_router(self) -> BaseRouter:
        app_module = importlib.import_module(self.app_module)
        raw_router = getattr(app_module, self.dialogs_router)
        if inspect.iscoroutinefunction(raw_router):
            router = await raw_router()
        elif inspect.isfunction(raw_router):
            router = raw_router()
        else:
            router = raw_router
        return cast(BaseRouter, router)

    async def _load_preview(self) -> str:
        router = await self._get_router()
        return await render_preview_content(router, simulate_events=True)

    async def _load_transitions(self, path: str) -> None:
        router = await self._get_router()
        name = removesuffix(path, ".png")
        render_transitions(router, filename=name)

    def load_preview(self) -> str:
        return asyncio.run(self._load_preview())

    def load_transitions(self, path: str) -> None:
        return asyncio.run(self._load_transitions(path))


class Controller:
    def __init__(self, app_module: str, dialogs_router: str) -> None:
        self.renderer = Renderer(app_module, dialogs_router)

    async def preview(self, _request: web.Request) -> web.Response:
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=1) as executor:
            text = await loop.run_in_executor(
                executor,
                self.renderer.load_preview,
            )
        return web.Response(
            text=text,
            headers={"Content-Type": "text/html"},
        )

    async def transitions(self, _request: web.Request) -> web.Response:
        loop = asyncio.get_running_loop()
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "transitions.png"
            with ProcessPoolExecutor(max_workers=1) as executor:
                try:
                    await loop.run_in_executor(
                        executor,
                        self.renderer.load_transitions,
                        str(path),
                    )
                except ImportError as exc:
                    return web.Response(status=500, text=str(exc))
            return web.Response(
                body=path.read_bytes(),
                headers={"Content-Type": "image/png"},
            )


PORT = 9876
INTRO = f"""
Maxo Dialog
====================

HTML preview:
http://127.0.0.1:{PORT}/

PNG transitions diagram:
http://127.0.0.1:{PORT}/transitions

======================
"""


def disable_print(*_args: Any, **_kwargs: Any) -> None:
    pass


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="maxo-dialog-preview",
        description="Локальный веб-сервер с HTML-превью и диаграммой переходов.",
    )
    parser.add_argument(
        "app",
        metavar="module:router",
        help="[путь/]модуль и имя роутера или фабрики, которая его возвращает",
    )
    args = parser.parse_args()
    app = args.app
    if os.path.altsep:
        app = app.replace(os.path.altsep, os.path.sep)
    path, _, app_spec = app.rpartition(os.path.sep)
    app_module, _, dialogs_router = app_spec.partition(":")
    if not app_module or not dialogs_router or ":" in dialogs_router:
        parser.error(f"ожидается формат module:router, получено {args.app!r}")
    if app_module.endswith(".py"):
        parser.error(f"укажите модуль без .py, получено {args.app!r}")
    directory = path or os.curdir
    sys.path.append(directory)
    try:
        module_spec = importlib.util.find_spec(app_module)
    except ImportError:
        module_spec = None
    if module_spec is None:
        parser.error(f"модуль {app_module!r} не найден в {directory!r}")
    controller = Controller(app_module, dialogs_router)
    routes = web.RouteTableDef()
    routes.get("/transitions")(controller.transitions)
    routes.get("/")(controller.preview)

    app = web.Application()
    app.add_routes(routes)
    print(INTRO)  # noqa: T201
    web.run_app(app, port=PORT, print=disable_print)
