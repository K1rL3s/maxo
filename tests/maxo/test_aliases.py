import importlib
import sys
import warnings

import pytest

import maxo

ALIASES = [
    ("maxo.exceptions", "maxo.errors"),
    ("maxo.filters", "maxo.routing.filters"),
    ("maxo.methods", "maxo.bot.methods"),
]


def test_top_level_all() -> None:
    # Extending top-level `maxo` is a maintainer decision
    assert set(maxo.__all__) == {
        "BaseMiddleware",
        "Bot",
        "Ctx",
        "Dispatcher",
        "Router",
        "__version__",
        "enums",
        "flags",
        "html",
        "md",
        "methods",
        "types",
    }
    for name in maxo.__all__:
        assert hasattr(maxo, name)


@pytest.mark.parametrize(("alias", "_"), ALIASES)
def test_permanent_alias_imports_without_warnings(alias: str, _: str) -> None:
    # aiogram aliases are permanent, warning about their removal would be a lie
    sys.modules.pop(alias, None)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        importlib.import_module(alias)


@pytest.mark.parametrize(("alias", "original"), ALIASES)
def test_alias_reexports_original(alias: str, original: str) -> None:
    alias_module = importlib.import_module(alias)
    original_module = importlib.import_module(original)
    for name in original_module.__all__:
        assert getattr(alias_module, name) is getattr(original_module, name)
