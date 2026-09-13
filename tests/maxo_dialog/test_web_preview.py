import importlib
import os.path
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from aiohttp import web

import maxo.dialogs.tools
from maxo.dialogs.tools import web_preview
from maxo.dialogs.tools.web_preview import Renderer, removesuffix
from maxo.routing.interfaces import BaseRouter


class DummyRouter:
    pass


def install_module(monkeypatch: pytest.MonkeyPatch, name: str, value: Any) -> None:
    module = ModuleType(name)
    module.__dict__["dialogs_router"] = value
    monkeypatch.setitem(sys.modules, name, module)


def test_removesuffix() -> None:
    assert removesuffix("diagram.png", ".png") == "diagram"
    assert removesuffix("diagram.svg", ".png") == "diagram.svg"


async def test_renderer_get_router_from_object(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_object", router)

    assert (
        await Renderer("test_preview_object", "dialogs_router")._get_router() is router
    )


async def test_renderer_get_router_from_sync_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_sync", lambda: router)

    assert await Renderer("test_preview_sync", "dialogs_router")._get_router() is router


async def test_renderer_get_router_from_async_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = cast(BaseRouter, DummyRouter())

    async def factory() -> BaseRouter:
        return router

    install_module(monkeypatch, "test_preview_async", factory)

    assert (
        await Renderer("test_preview_async", "dialogs_router")._get_router() is router
    )


async def test_renderer_load_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    install_module(monkeypatch, "test_preview_load", router)

    async def render_preview_content(
        loaded_router: BaseRouter,
        simulate_events: bool,
    ) -> str:
        assert loaded_router is router
        assert simulate_events is True
        return "<html></html>"

    monkeypatch.setattr(web_preview, "render_preview_content", render_preview_content)

    assert await Renderer("test_preview_load", "dialogs_router")._load_preview() == (
        "<html></html>"
    )


async def test_renderer_load_transitions(monkeypatch: pytest.MonkeyPatch) -> None:
    router = cast(BaseRouter, DummyRouter())
    called: dict[str, Any] = {}
    install_module(monkeypatch, "test_preview_transitions", router)

    def render_transitions(loaded_router: BaseRouter, filename: str) -> None:
        called["router"] = loaded_router
        called["filename"] = filename

    monkeypatch.setattr(web_preview, "render_transitions", render_transitions)

    await Renderer("test_preview_transitions", "dialogs_router")._load_transitions(
        "diagram.png",
    )

    assert called == {"router": router, "filename": "diagram"}


def test_disable_print_swallows_everything() -> None:
    web_preview.disable_print("a", b=1)


def test_load_preview_runs_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = Renderer("m", "r")

    async def fake_load_preview() -> str:
        return "<html/>"

    monkeypatch.setattr(renderer, "_load_preview", fake_load_preview)

    assert renderer.load_preview() == "<html/>"


def test_load_transitions_runs_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    renderer = Renderer("m", "r")
    called: list[str] = []

    async def fake_load_transitions(path: str) -> None:
        called.append(path)

    monkeypatch.setattr(renderer, "_load_transitions", fake_load_transitions)
    renderer.load_transitions("d.png")

    assert called == ["d.png"]


class ImmediateExecutor:
    """Заменяет ProcessPoolExecutor: пикл не нужен, работаем в потоке."""

    def __enter__(self) -> ThreadPoolExecutor:
        self._executor = ThreadPoolExecutor(max_workers=1)
        return self._executor

    def __exit__(self, *_args: object) -> None:
        self._executor.shutdown()


async def test_controller_preview(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        web_preview,
        "ProcessPoolExecutor",
        lambda **_kwargs: ImmediateExecutor(),
    )
    controller = web_preview.Controller("m", "r")
    monkeypatch.setattr(controller.renderer, "load_preview", lambda: "<html/>")

    response = await controller.preview(cast(Any, None))

    assert response.text == "<html/>"
    assert response.headers["Content-Type"].startswith("text/html")


async def test_controller_transitions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        web_preview,
        "ProcessPoolExecutor",
        lambda **_kwargs: ImmediateExecutor(),
    )
    controller = web_preview.Controller("m", "r")

    def load_transitions(path: str) -> None:
        Path(path).write_bytes(b"PNG")

    monkeypatch.setattr(controller.renderer, "load_transitions", load_transitions)

    response = await controller.transitions(cast(Any, None))

    assert response.body == b"PNG"
    assert response.headers["Content-Type"] == "image/png"


def test_main_registers_routes_and_runs_app(monkeypatch: pytest.MonkeyPatch) -> None:
    started: dict[str, Any] = {}
    monkeypatch.setattr(sys, "path", list(sys.path))

    def run_app(app: Any, port: int, print: Any) -> None:
        started["port"] = port
        started["app"] = app

    monkeypatch.setattr(web, "run_app", run_app)
    monkeypatch.setattr(sys, "argv", ["maxo-dialog-preview", "bot:dialogs_router"])

    web_preview.main()

    assert started["port"] == web_preview.PORT


def noop_run_app(*_args: Any, **_kwargs: Any) -> None:
    pass


def test_main_appends_module_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    paths: list[str] = []
    monkeypatch.setattr(web, "run_app", noop_run_app)
    monkeypatch.setattr(sys, "path", paths)
    monkeypatch.setattr(
        sys,
        "argv",
        ["maxo-dialog-preview", f"pkg{os.path.sep}bot:dialogs_router"],
    )

    web_preview.main()

    assert paths == ["pkg"]


def test_web_preview_imports_without_diagrams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "diagrams", None)
    for name in list(sys.modules):
        if name.startswith("maxo.dialogs.tools"):
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setattr(maxo.dialogs, "tools", maxo.dialogs.tools)

    module = importlib.import_module("maxo.dialogs.tools.web_preview")

    assert callable(module.main)


def test_main_help(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        web_preview.main(["--help"])

    assert exc_info.value.code == 0
    assert "module:router" in capsys.readouterr().out


@pytest.mark.parametrize("argv", [[], ["bot"], ["bot:"], [":router"], ["a:b:c"]])
def test_main_rejects_invalid_app_spec(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        web_preview.main(argv)

    assert exc_info.value.code == 2
    assert "usage:" in capsys.readouterr().err
