import importlib
import sys
import warnings
from types import ModuleType

from maxo.errors import MaxoError
from maxo.routing.filters import BaseFilter


def import_alias_module(name: str) -> ModuleType:
    """Импортировать алиас заново и убедиться, что он не предупреждает."""
    sys.modules.pop(name, None)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        return importlib.import_module(name)


def test_exceptions_alias_exports_errors() -> None:
    module = import_alias_module("maxo.exceptions")

    assert module.MaxoError is MaxoError
    assert "MaxoError" in module.__all__


def test_filters_alias_exports_routing_filters() -> None:
    module = import_alias_module("maxo.filters")

    assert module.BaseFilter is BaseFilter
    assert "BaseFilter" in module.__all__
